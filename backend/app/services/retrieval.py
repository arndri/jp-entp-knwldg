import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass

from qdrant_client.http import models
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Document, DocumentChunk
from app.schemas.rag import Citation
from app.services.embeddings import get_embedder
from app.services.vector_store import get_qdrant_client


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+|[\u3040-\u30ff\u3400-\u9fff]")


@dataclass(frozen=True)
class ChunkCandidate:
    chunk_id: str
    document_id: str
    title: str
    page_number: int
    text: str
    score: float


def tokenize(text: str) -> list[str]:
    base_tokens = TOKEN_PATTERN.findall(text.lower())
    cjk_chars = [token for token in base_tokens if len(token) == 1 and not token.isascii()]
    bigrams = [
        "".join(pair)
        for pair in zip(cjk_chars, cjk_chars[1:], strict=False)
    ]
    return base_tokens + bigrams


def citation_from_candidate(candidate: ChunkCandidate, score: float | None = None) -> Citation:
    return Citation(
        document_id=candidate.document_id,
        title=candidate.title,
        page_number=candidate.page_number,
        chunk_id=candidate.chunk_id,
        excerpt=candidate.text[:500],
        score=score if score is not None else candidate.score,
    )


def vector_search(question: str, access_levels: list[str], limit: int) -> list[Citation]:
    settings = get_settings()
    query_vector = get_embedder().embed([question])[0]
    client = get_qdrant_client()

    hits = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        limit=limit,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="access_level",
                    match=models.MatchAny(any=access_levels),
                )
            ]
        ),
    )

    citations: list[Citation] = []
    for hit in hits:
        payload = hit.payload or {}
        citations.append(
            Citation(
                document_id=str(payload.get("document_id", "")),
                title=str(payload.get("title", "")),
                page_number=int(payload.get("page_number", 0)),
                chunk_id=str(payload.get("chunk_id", hit.id)),
                excerpt=str(payload.get("text", ""))[:500],
                score=float(hit.score) if hit.score is not None else None,
            )
        )
    return citations


def load_authorized_chunks(session: Session, access_levels: list[str]) -> list[ChunkCandidate]:
    rows = session.execute(
        select(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(Document.access_level.in_(access_levels))
        .where(Document.status == "indexed")
    ).all()
    return [
        ChunkCandidate(
            chunk_id=chunk.id,
            document_id=document.id,
            title=document.title,
            page_number=chunk.page_number,
            text=chunk.chunk_text,
            score=0.0,
        )
        for chunk, document in rows
    ]


def bm25_search(
    question: str,
    access_levels: list[str],
    session: Session,
    limit: int,
) -> list[Citation]:
    candidates = load_authorized_chunks(session, access_levels)
    if not candidates:
        return []

    query_tokens = tokenize(question)
    if not query_tokens:
        return []

    docs_tokens = [tokenize(candidate.text) for candidate in candidates]
    doc_count = len(docs_tokens)
    avg_doc_len = sum(len(tokens) for tokens in docs_tokens) / doc_count
    doc_freq: Counter[str] = Counter()
    for tokens in docs_tokens:
        doc_freq.update(set(tokens))

    query_counts = Counter(query_tokens)
    k1 = 1.5
    b = 0.75
    scored: list[ChunkCandidate] = []

    for candidate, tokens in zip(candidates, docs_tokens, strict=True):
        if not tokens:
            continue
        term_counts = Counter(tokens)
        doc_len = len(tokens)
        score = 0.0
        for token, query_count in query_counts.items():
            frequency = term_counts[token]
            if frequency == 0:
                continue
            idf = math.log(1 + (doc_count - doc_freq[token] + 0.5) / (doc_freq[token] + 0.5))
            denominator = frequency + k1 * (1 - b + b * doc_len / avg_doc_len)
            score += idf * (frequency * (k1 + 1) / denominator) * query_count
        if score > 0:
            scored.append(
                ChunkCandidate(
                    chunk_id=candidate.chunk_id,
                    document_id=candidate.document_id,
                    title=candidate.title,
                    page_number=candidate.page_number,
                    text=candidate.text,
                    score=score,
                )
            )

    scored.sort(key=lambda candidate: candidate.score, reverse=True)
    top = scored[:limit]
    max_score = top[0].score if top else 0.0
    return [
        citation_from_candidate(candidate, candidate.score / max_score if max_score else 0.0)
        for candidate in top
    ]


def reciprocal_rank_fusion(
    ranked_lists: list[list[Citation]],
    final_limit: int,
) -> list[Citation]:
    settings = get_settings()
    fused_scores: defaultdict[str, float] = defaultdict(float)
    citation_by_id: dict[str, Citation] = {}

    for ranked in ranked_lists:
        for rank, citation in enumerate(ranked, start=1):
            fused_scores[citation.chunk_id] += 1 / (settings.rrf_k + rank)
            citation_by_id.setdefault(citation.chunk_id, citation)

    ranked_ids = sorted(fused_scores, key=lambda chunk_id: fused_scores[chunk_id], reverse=True)
    top_ids = ranked_ids[:final_limit]
    max_score = fused_scores[top_ids[0]] if top_ids else 0.0
    fused: list[Citation] = []
    for chunk_id in top_ids:
        citation = citation_by_id[chunk_id]
        fused.append(
            Citation(
                document_id=citation.document_id,
                title=citation.title,
                page_number=citation.page_number,
                chunk_id=citation.chunk_id,
                excerpt=citation.excerpt,
                score=fused_scores[chunk_id] / max_score if max_score else 0.0,
            )
        )
    return fused


def retrieve(
    question: str,
    access_levels: list[str],
    session: Session | None = None,
) -> list[Citation]:
    settings = get_settings()
    vector_results = vector_search(question, access_levels, settings.vector_candidate_limit)
    if settings.retrieval_mode == "vector" or session is None:
        return vector_results[: settings.max_context_chunks]
    if settings.retrieval_mode != "hybrid":
        raise ValueError(f"Unsupported retrieval mode: {settings.retrieval_mode}")

    bm25_results = bm25_search(
        question,
        access_levels,
        session,
        settings.bm25_candidate_limit,
    )
    return reciprocal_rank_fusion(
        [vector_results, bm25_results],
        settings.max_context_chunks,
    )
