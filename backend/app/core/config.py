from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5-mini", alias="OPENAI_MODEL")

    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: str = Field(default="", alias="QDRANT_API_KEY")
    qdrant_collection: str = "jp_enterprise_chunks"

    embedding_provider: str = Field(default="local", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="BAAI/bge-m3", alias="EMBEDDING_MODEL")
    hf_token: str = Field(default="", alias="HF_TOKEN")
    document_extractor: str = Field(default="pypdf", alias="DOCUMENT_EXTRACTOR")
    docling_do_ocr: bool = Field(default=False, alias="DOCLING_DO_OCR")
    docling_device: str = Field(default="cpu", alias="DOCLING_DEVICE")
    docling_fallback_to_pypdf: bool = Field(default=True, alias="DOCLING_FALLBACK_TO_PYPDF")
    docling_layout_batch_size: int = Field(default=1, alias="DOCLING_LAYOUT_BATCH_SIZE")
    docling_ocr_batch_size: int = Field(default=1, alias="DOCLING_OCR_BATCH_SIZE")
    docling_table_batch_size: int = Field(default=1, alias="DOCLING_TABLE_BATCH_SIZE")
    docling_max_pages: int = Field(default=15, alias="DOCLING_MAX_PAGES")

    max_context_chunks: int = 6
    chunk_size: int = 900
    chunk_overlap: int = 150


@lru_cache
def get_settings() -> Settings:
    return Settings()
