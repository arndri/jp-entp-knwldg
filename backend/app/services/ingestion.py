from pathlib import Path
from uuid import uuid4

from qdrant_client.http import models
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.config import ROOT_DIR, get_settings
from app.models import Document, DocumentChunk, IngestionJob, utc_now
from app.schemas.rag import IngestResponse
from app.services.chunking import chunk_pages
from app.services.embeddings import get_embedder
from app.services.extraction import get_page_extractor
from app.services.retrieval import clear_bm25_cache, warm_bm25_cache
from app.services.vector_store import delete_document_chunks, get_qdrant_client, upsert_chunks


def resolve_document_path(path_value: str) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT_DIR / path
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError("MVP ingestion currently supports PDF files only.")
    return path


def ingest_pdf(
    path_value: str,
    access_level: str,
    session: Session,
    document: Document | None = None,
) -> IngestResponse:
    settings = get_settings()
    path = resolve_document_path(path_value)
    if document is None:
        document = Document(title=path.name, source_path=str(path), access_level=access_level)
        session.add(document)
        session.flush()
    else:
        document.title = path.name
        document.source_path = str(path)
        document.access_level = access_level

    document.status = "processing"
    document.error_message = None
    job = IngestionJob(document_id=document.id, status="processing")
    session.add(job)
    session.commit()

    try:
        pages = get_page_extractor().extract_pages(path)
        if not pages:
            raise ValueError(
                "No text was extracted. Try enabling Docling OCR for scanned PDFs."
            )

        chunks = chunk_pages(pages, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            raise ValueError("No chunks were produced from the document.")

        embedder = get_embedder()
        vectors = embedder.embed([chunk.text for chunk in chunks])
        vector_size = len(vectors[0])

        points: list[models.PointStruct] = []
        db_chunks: list[DocumentChunk] = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            chunk_id = str(uuid4())
            points.append(
                models.PointStruct(
                    id=chunk_id,
                    vector=vector,
                    payload={
                        "chunk_id": chunk_id,
                        "document_id": document.id,
                        "title": path.name,
                        "source_path": str(path),
                        "page_number": chunk.page_number,
                        "text": chunk.text,
                        "access_level": access_level,
                    },
                )
            )
            db_chunks.append(
                DocumentChunk(
                    id=chunk_id,
                    document_id=document.id,
                    page_number=chunk.page_number,
                    chunk_text=chunk.text,
                    embedding_id=chunk_id,
                )
            )

        delete_document_chunks(document.id)
        client = get_qdrant_client()
        upsert_chunks(client, settings.qdrant_collection, points, vector_size)

        session.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document.id)
        )
        session.add_all(db_chunks)
        document.status = "indexed"
        document.chunk_count = len(points)
        document.indexed_at = utc_now()
        job.status = "completed"
        job.chunk_count = len(points)
        job.completed_at = utc_now()
        session.commit()
        clear_bm25_cache()
        warm_bm25_cache(session, [access_level])
    except Exception as exc:
        session.rollback()
        document = session.get(Document, document.id)
        job = session.get(IngestionJob, job.id)
        if document is not None:
            document.status = "failed"
            document.error_message = str(exc)
        if job is not None:
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = utc_now()
        session.commit()
        raise

    return IngestResponse(
        document_id=document.id,
        title=path.name,
        chunks_indexed=len(points),
    )
