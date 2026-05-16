from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db_session
from app.schemas.rag import (
    ChatRequest,
    ChatResponse,
    DocumentResponse,
    IngestRequest,
    IngestResponse,
    LoginRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import (
    allowed_access_levels,
    authenticate_user,
    create_access_token,
    get_current_user,
    require_admin,
    to_user_response,
)
from app.services.documents import delete_document, get_document, list_documents
from app.services.ingestion import ingest_pdf
from app.services.llm import generate_answer
from app.services.retrieval import retrieve

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/auth/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    session: Session = Depends(get_db_session),
) -> TokenResponse:
    user = authenticate_user(session, request.email, request.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return TokenResponse(access_token=create_access_token(user))


@router.get("/auth/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)) -> UserResponse:
    return to_user_response(current_user)


@router.post("/ingest", response_model=IngestResponse)
def ingest(
    request: IngestRequest,
    session: Session = Depends(get_db_session),
    _: object = Depends(require_admin),
) -> IngestResponse:
    try:
        return ingest_pdf(request.path, request.access_level, session)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/documents", response_model=list[DocumentResponse])
def documents(
    session: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[DocumentResponse]:
    return list_documents(session, allowed_access_levels(current_user))


@router.delete("/documents/{document_id}", status_code=204)
def remove_document(
    document_id: str,
    session: Session = Depends(get_db_session),
    _: object = Depends(require_admin),
) -> None:
    document = get_document(session, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    delete_document(session, document)


@router.post("/documents/{document_id}/reindex", response_model=IngestResponse)
def reindex_document(
    document_id: str,
    session: Session = Depends(get_db_session),
    _: object = Depends(require_admin),
) -> IngestResponse:
    document = get_document(session, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    try:
        return ingest_pdf(document.source_path, document.access_level, session, document)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user=Depends(get_current_user),
) -> ChatResponse:
    try:
        citations = retrieve(request.question, allowed_access_levels(current_user))
        if not citations:
            return ChatResponse(
                answer="I could not find relevant authorized document context for this question.",
                citations=[],
            )
        answer = generate_answer(request.question, citations)
        return ChatResponse(answer=answer, citations=citations)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
