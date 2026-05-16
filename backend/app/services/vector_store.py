from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.core.config import get_settings


def get_qdrant_client() -> QdrantClient:
    settings = get_settings()
    api_key = settings.qdrant_api_key or None
    return QdrantClient(url=settings.qdrant_url, api_key=api_key)


def ensure_collection(client: QdrantClient, collection_name: str, vector_size: int) -> None:
    collections = client.get_collections().collections
    if any(collection.name == collection_name for collection in collections):
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
    )


def upsert_chunks(
    client: QdrantClient,
    collection_name: str,
    points: list[models.PointStruct],
    vector_size: int,
) -> None:
    ensure_collection(client, collection_name, vector_size)
    client.upsert(collection_name=collection_name, points=points)


def delete_document_chunks(document_id: str) -> None:
    settings = get_settings()
    client = get_qdrant_client()
    collections = client.get_collections().collections
    if not any(collection.name == settings.qdrant_collection for collection in collections):
        return
    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=document_id),
                    )
                ]
            )
        ),
    )
