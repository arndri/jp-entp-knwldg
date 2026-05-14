from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    path: str = Field(..., description="PDF path relative to project root or absolute path.")
    access_level: str = "public"


class IngestResponse(BaseModel):
    document_id: str
    title: str
    chunks_indexed: int


class Citation(BaseModel):
    document_id: str
    title: str
    page_number: int
    chunk_id: str
    excerpt: str
    score: float | None = None


class ChatRequest(BaseModel):
    question: str
    access_levels: list[str] = Field(default_factory=lambda: ["public"])


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]

