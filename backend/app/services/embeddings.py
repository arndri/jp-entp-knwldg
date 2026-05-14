from functools import lru_cache

import numpy as np

from app.core.config import get_settings


class LocalBgeM3Embeddings:
    def __init__(self, model_name: str, hf_token: str = "") -> None:
        from sentence_transformers import SentenceTransformer
        import torch

        token = hf_token or None
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(
            model_name,
            trust_remote_code=True,
            token=token,
            device=device,
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(
            texts,
            batch_size=8,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        if isinstance(vectors, np.ndarray):
            return vectors.astype(float).tolist()
        return [np.asarray(vector, dtype=float).tolist() for vector in vectors]


@lru_cache
def get_embedder() -> LocalBgeM3Embeddings:
    settings = get_settings()
    if settings.embedding_provider != "local":
        raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")
    return LocalBgeM3Embeddings(settings.embedding_model, settings.hf_token)
