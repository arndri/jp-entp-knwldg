from types import SimpleNamespace

from app.schemas.rag import Citation
from app.services import retrieval


def test_tokenize_adds_japanese_bigrams() -> None:
    tokens = retrieval.tokenize("特定技能制度")

    assert "特" in tokens
    assert "特定" in tokens
    assert "技能" in tokens


def test_reciprocal_rank_fusion_normalizes_scores(monkeypatch) -> None:
    monkeypatch.setattr(
        retrieval,
        "get_settings",
        lambda: SimpleNamespace(rrf_k=60),
    )
    vector = [
        Citation(
            document_id="doc-1",
            title="sample.pdf",
            page_number=1,
            chunk_id="a",
            excerpt="A",
            score=0.9,
        )
    ]
    bm25 = [
        Citation(
            document_id="doc-1",
            title="sample.pdf",
            page_number=2,
            chunk_id="b",
            excerpt="B",
            score=1.0,
        ),
        Citation(
            document_id="doc-1",
            title="sample.pdf",
            page_number=1,
            chunk_id="a",
            excerpt="A",
            score=0.8,
        ),
    ]

    fused = retrieval.reciprocal_rank_fusion([vector, bm25], final_limit=2)

    assert fused[0].chunk_id == "a"
    assert fused[0].score == 1.0
    assert len(fused) == 2


def test_retrieve_hybrid_fuses_vector_and_bm25(monkeypatch) -> None:
    monkeypatch.setattr(
        retrieval,
        "get_settings",
        lambda: SimpleNamespace(
            retrieval_mode="hybrid",
            vector_candidate_limit=2,
            bm25_candidate_limit=2,
            max_context_chunks=2,
            rrf_k=60,
        ),
    )
    monkeypatch.setattr(
        retrieval,
        "vector_search",
        lambda question, access_levels, limit: [
            Citation(
                document_id="doc-1",
                title="vector.pdf",
                page_number=1,
                chunk_id="vector",
                excerpt="vector",
                score=0.9,
            )
        ],
    )
    monkeypatch.setattr(
        retrieval,
        "bm25_search",
        lambda question, access_levels, session, limit: [
            Citation(
                document_id="doc-2",
                title="bm25.pdf",
                page_number=2,
                chunk_id="bm25",
                excerpt="bm25",
                score=1.0,
            )
        ],
    )

    results = retrieval.retrieve("question", ["public"], session=object())

    assert {citation.chunk_id for citation in results} == {"vector", "bm25"}


def test_bm25_search_reuses_cached_index(monkeypatch) -> None:
    retrieval.clear_bm25_cache()
    calls = {"load": 0}
    candidates = [
        retrieval.ChunkCandidate(
            chunk_id="chunk-1",
            document_id="doc-1",
            title="sample.pdf",
            page_number=1,
            text="特定技能制度 申請 書類",
            score=0.0,
        )
    ]

    def fake_load(session, access_levels):
        calls["load"] += 1
        return candidates

    monkeypatch.setattr(retrieval, "load_authorized_chunks", fake_load)

    first = retrieval.bm25_search("特定技能 申請", ["public"], object(), 5)
    second = retrieval.bm25_search("制度 書類", ["public"], object(), 5)

    assert calls["load"] == 1
    assert first[0].chunk_id == "chunk-1"
    assert second[0].chunk_id == "chunk-1"
    retrieval.clear_bm25_cache()
