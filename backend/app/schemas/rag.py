from datetime import datetime

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    path: str = Field(..., description="PDF path relative to project root or absolute path.")
    access_level: str = "public"


class IngestResponse(BaseModel):
    document_id: str
    title: str
    chunks_indexed: int


class DocumentResponse(BaseModel):
    document_id: str
    title: str
    source_path: str
    access_level: str
    status: str
    chunks_indexed: int
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    indexed_at: datetime | None = None
    latest_job_status: str | None = None


class Citation(BaseModel):
    document_id: str
    title: str
    page_number: int
    chunk_id: str
    excerpt: str
    score: float | None = None


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    user_id: str
    email: str
    role: str


class EvaluationRunRequest(BaseModel):
    name: str = "retrieval-eval"
    question_set_path: str = "eval/questions.local.jsonl"
    top_k: int = 5
    access_levels: list[str] = Field(default_factory=lambda: ["public"])


class EvaluationItemResponse(BaseModel):
    question_id: str
    question: str
    expected_document: str
    expected_pages: list[int]
    retrieved_document: str | None = None
    retrieved_page: int | None = None
    rank: int | None = None
    reciprocal_rank: float
    latency_ms: float
    hit: bool


class EvaluationRunResponse(BaseModel):
    run_id: str
    name: str
    question_set_path: str
    top_k: int
    access_levels: list[str]
    question_count: int
    hit_count: int
    recall_at_k: float
    mrr: float
    average_latency_ms: float
    status: str
    error_message: str | None = None
    created_at: datetime
    items: list[EvaluationItemResponse] = Field(default_factory=list)
