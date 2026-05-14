from qdrant_client.http import models

from app.core.config import get_settings
from app.schemas.rag import Citation
from app.services.embeddings import get_embedder
from app.services.vector_store import get_qdrant_client


def retrieve(question: str, access_levels: list[str]) -> list[Citation]:
    settings = get_settings()
    query_vector = get_embedder().embed([question])[0]
    client = get_qdrant_client()

    hits = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        limit=settings.max_context_chunks,
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

