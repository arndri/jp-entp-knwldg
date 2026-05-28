from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(255))
    source_path: Mapped[str] = mapped_column(Text)
    access_level: Mapped[str] = mapped_column(String(64), default="public")
    status: Mapped[str] = mapped_column(String(32), default="pending")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
    ingestion_jobs: Mapped[list["IngestionJob"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(32), default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    page_number: Mapped[int] = mapped_column(Integer)
    chunk_text: Mapped[str] = mapped_column(Text)
    embedding_id: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    document: Mapped[Document] = relationship(back_populates="chunks")


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), default="pending")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    document: Mapped[Document] = relationship(back_populates="ingestion_jobs")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    question_set_path: Mapped[str] = mapped_column(Text)
    top_k: Mapped[int] = mapped_column(Integer, default=5)
    access_levels: Mapped[str] = mapped_column(Text)
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    hit_count: Mapped[int] = mapped_column(Integer, default=0)
    recall_at_k: Mapped[float] = mapped_column(Float, default=0.0)
    mrr: Mapped[float] = mapped_column(Float, default=0.0)
    average_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="completed")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    items: Mapped[list["EvaluationItem"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )


class EvaluationItem(Base):
    __tablename__ = "evaluation_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    run_id: Mapped[str] = mapped_column(
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        index=True,
    )
    question_id: Mapped[str] = mapped_column(String(255))
    question: Mapped[str] = mapped_column(Text)
    expected_document: Mapped[str] = mapped_column(String(255))
    expected_pages: Mapped[str] = mapped_column(Text)
    retrieved_document: Mapped[str | None] = mapped_column(String(255), nullable=True)
    retrieved_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reciprocal_rank: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)

    run: Mapped[EvaluationRun] = relationship(back_populates="items")
