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
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    deepseek_model: str = Field(default="deepseek-v4-flash", alias="DEEPSEEK_MODEL")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com",
        alias="DEEPSEEK_BASE_URL",
    )

    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: str = Field(default="", alias="QDRANT_API_KEY")
    qdrant_collection: str = "jp_enterprise_chunks"
    database_url: str = Field(
        default="postgresql+psycopg://postgres:123@localhost:5432/jp_enterprise_knowledge",
        alias="DATABASE_URL",
    )
    jwt_secret_key: str = Field(default="", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=480, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    bootstrap_admin_email: str = Field(default="admin@example.com", alias="BOOTSTRAP_ADMIN_EMAIL")
    bootstrap_admin_password: str = Field(default="admin12345", alias="BOOTSTRAP_ADMIN_PASSWORD")
    bootstrap_user_email: str = Field(default="user@example.com", alias="BOOTSTRAP_USER_EMAIL")
    bootstrap_user_password: str = Field(default="user12345", alias="BOOTSTRAP_USER_PASSWORD")

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
    max_question_chars: int = Field(default=1200, alias="MAX_QUESTION_CHARS")
    min_retrieval_score: float = Field(default=0.35, alias="MIN_RETRIEVAL_SCORE")
    enable_prompt_injection_filter: bool = Field(
        default=True,
        alias="ENABLE_PROMPT_INJECTION_FILTER",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
