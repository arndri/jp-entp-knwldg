from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Document
from app.schemas.rag import DocumentResponse
from app.services.retrieval import clear_bm25_cache
from app.services.vector_store import delete_document_chunks


def to_document_response(document: Document) -> DocumentResponse:
    latest_job = max(
        document.ingestion_jobs,
        key=lambda job: job.started_at,
        default=None,
    )
    return DocumentResponse(
        document_id=document.id,
        title=document.title,
        source_path=document.source_path,
        access_level=document.access_level,
        status=document.status,
        chunks_indexed=document.chunk_count,
        error_message=document.error_message,
        created_at=document.created_at,
        updated_at=document.updated_at,
        indexed_at=document.indexed_at,
        latest_job_status=latest_job.status if latest_job else None,
    )


def list_documents(session: Session, access_levels: list[str]) -> list[DocumentResponse]:
    documents = session.scalars(
        select(Document)
        .options(selectinload(Document.ingestion_jobs))
        .where(Document.access_level.in_(access_levels))
        .order_by(Document.created_at.desc())
    ).all()
    return [to_document_response(document) for document in documents]


def get_document(session: Session, document_id: str) -> Document | None:
    return session.get(Document, document_id)


def delete_document(session: Session, document: Document) -> None:
    delete_document_chunks(document.id)
    session.delete(document)
    session.commit()
    clear_bm25_cache()
