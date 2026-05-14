from pathlib import Path
from uuid import uuid4

from qdrant_client.http import models

from app.core.config import ROOT_DIR, get_settings
from app.schemas.rag import IngestResponse
from app.services.chunking import chunk_pages
from app.services.embeddings import get_embedder
from app.services.pdf import extract_pdf_pages
from app.services.vector_store import get_qdrant_client, upsert_chunks


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


def ingest_pdf(path_value: str, access_level: str) -> IngestResponse:
    settings = get_settings()
    path = resolve_document_path(path_value)
    pages = extract_pdf_pages(path)
    if not pages:
        raise ValueError(
            "No text was extracted. This PDF may be scanned; OCR will be added in the next pipeline phase."
        )

    chunks = chunk_pages(pages, settings.chunk_size, settings.chunk_overlap)
    if not chunks:
        raise ValueError("No chunks were produced from the document.")

    embedder = get_embedder()
    vectors = embedder.embed([chunk.text for chunk in chunks])
    vector_size = len(vectors[0])

    document_id = str(uuid4())
    points: list[models.PointStruct] = []
    for chunk, vector in zip(chunks, vectors, strict=True):
        chunk_id = str(uuid4())
        points.append(
            models.PointStruct(
                id=chunk_id,
                vector=vector,
                payload={
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "title": path.name,
                    "source_path": str(path),
                    "page_number": chunk.page_number,
                    "text": chunk.text,
                    "access_level": access_level,
                },
            )
        )

    client = get_qdrant_client()
    upsert_chunks(client, settings.qdrant_collection, points, vector_size)

    return IngestResponse(document_id=document_id, title=path.name, chunks_indexed=len(points))

