from fastapi import APIRouter, HTTPException

from app.schemas.rag import ChatRequest, ChatResponse, IngestRequest, IngestResponse
from app.services.ingestion import ingest_pdf
from app.services.llm import generate_answer
from app.services.retrieval import retrieve

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest) -> IngestResponse:
    try:
        return ingest_pdf(request.path, request.access_level)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        citations = retrieve(request.question, request.access_levels)
        if not citations:
            return ChatResponse(
                answer="I could not find relevant authorized document context for this question.",
                citations=[],
            )
        answer = generate_answer(request.question, citations)
        return ChatResponse(answer=answer, citations=citations)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

