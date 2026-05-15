from fastapi.testclient import TestClient

from app.main import app
from app.schemas.rag import Citation, IngestResponse


client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ingest_returns_service_response(monkeypatch) -> None:
    def fake_ingest(path: str, access_level: str) -> IngestResponse:
        assert path == "sample.pdf"
        assert access_level == "public"
        return IngestResponse(document_id="doc-1", title="sample.pdf", chunks_indexed=3)

    monkeypatch.setattr("app.api.routes.ingest_pdf", fake_ingest)

    response = client.post("/api/ingest", json={"path": "sample.pdf", "access_level": "public"})

    assert response.status_code == 200
    assert response.json() == {
        "document_id": "doc-1",
        "title": "sample.pdf",
        "chunks_indexed": 3,
    }


def test_chat_returns_empty_answer_when_no_authorized_context(monkeypatch) -> None:
    monkeypatch.setattr("app.api.routes.retrieve", lambda question, access_levels: [])

    response = client.post("/api/chat", json={"question": "hello", "access_levels": ["public"]})

    assert response.status_code == 200
    assert response.json() == {
        "answer": "I could not find relevant authorized document context for this question.",
        "citations": [],
    }


def test_chat_returns_generated_answer_with_citations(monkeypatch) -> None:
    citations = [
        Citation(
            document_id="doc-1",
            title="sample.pdf",
            page_number=4,
            chunk_id="chunk-1",
            excerpt="Relevant text",
            score=0.91,
        )
    ]
    monkeypatch.setattr("app.api.routes.retrieve", lambda question, access_levels: citations)
    monkeypatch.setattr("app.api.routes.generate_answer", lambda question, found: "Grounded answer [1]")

    response = client.post("/api/chat", json={"question": "hello", "access_levels": ["public"]})

    assert response.status_code == 200
    assert response.json()["answer"] == "Grounded answer [1]"
    assert response.json()["citations"][0]["title"] == "sample.pdf"

