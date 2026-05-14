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

