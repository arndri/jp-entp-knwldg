import json
import time
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import ROOT_DIR
from app.models import EvaluationItem, EvaluationRun, User
from app.schemas.rag import (
    EvaluationItemResponse,
    EvaluationRunRequest,
    EvaluationRunResponse,
)
from app.services.retrieval import retrieve


@dataclass(frozen=True)
class EvalQuestion:
    id: str
    question: str
    expected_document: str
    expected_pages: set[int]


def resolve_question_set(path_value: str) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT_DIR / path
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"Evaluation question set not found: {path}")
    return path


def load_eval_questions(path: Path) -> list[EvalQuestion]:
    questions: list[EvalQuestion] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        questions.append(
            EvalQuestion(
                id=str(raw["id"]),
                question=str(raw["question"]),
                expected_document=str(raw["expected_document"]),
                expected_pages={int(page) for page in raw["expected_pages"]},
            )
        )
    if not questions:
        raise ValueError("No evaluation questions found.")
    return questions


def to_item_response(item: EvaluationItem) -> EvaluationItemResponse:
    expected_pages = [int(page) for page in json.loads(item.expected_pages)]
    return EvaluationItemResponse(
        question_id=item.question_id,
        question=item.question,
        expected_document=item.expected_document,
        expected_pages=expected_pages,
        retrieved_document=item.retrieved_document,
        retrieved_page=item.retrieved_page,
        rank=item.rank,
        reciprocal_rank=item.reciprocal_rank,
        latency_ms=item.latency_ms,
        hit=item.rank is not None,
    )


def to_run_response(run: EvaluationRun, include_items: bool = True) -> EvaluationRunResponse:
    return EvaluationRunResponse(
        run_id=run.id,
        name=run.name,
        question_set_path=run.question_set_path,
        top_k=run.top_k,
        access_levels=list(json.loads(run.access_levels)),
        question_count=run.question_count,
        hit_count=run.hit_count,
        recall_at_k=run.recall_at_k,
        mrr=run.mrr,
        average_latency_ms=run.average_latency_ms,
        status=run.status,
        error_message=run.error_message,
        created_at=run.created_at,
        items=[to_item_response(item) for item in run.items] if include_items else [],
    )


def run_retrieval_evaluation(
    session: Session,
    request: EvaluationRunRequest,
    user: User,
) -> EvaluationRunResponse:
    path = resolve_question_set(request.question_set_path)
    questions = load_eval_questions(path)

    run = EvaluationRun(
        name=request.name,
        question_set_path=str(path),
        top_k=request.top_k,
        access_levels=json.dumps(request.access_levels),
        question_count=len(questions),
        created_by=user.id,
    )
    session.add(run)
    session.flush()

    hit_count = 0
    reciprocal_rank_total = 0.0
    latency_total = 0.0
    items: list[EvaluationItem] = []

    for question in questions:
        started = time.perf_counter()
        citations = retrieve(
            question.question,
            request.access_levels,
            session=session,
        )[: request.top_k]
        latency_ms = (time.perf_counter() - started) * 1000
        latency_total += latency_ms

        rank = next(
            (
                index
                for index, citation in enumerate(citations, start=1)
                if citation.title == question.expected_document
                and citation.page_number in question.expected_pages
            ),
            None,
        )
        reciprocal_rank = 1 / rank if rank is not None else 0.0
        if rank is not None:
            hit_count += 1
            reciprocal_rank_total += reciprocal_rank

        top_citation = citations[0] if citations else None
        items.append(
            EvaluationItem(
                run_id=run.id,
                question_id=question.id,
                question=question.question,
                expected_document=question.expected_document,
                expected_pages=json.dumps(sorted(question.expected_pages)),
                retrieved_document=top_citation.title if top_citation else None,
                retrieved_page=top_citation.page_number if top_citation else None,
                rank=rank,
                reciprocal_rank=reciprocal_rank,
                latency_ms=latency_ms,
            )
        )

    total = len(questions)
    run.hit_count = hit_count
    run.recall_at_k = hit_count / total
    run.mrr = reciprocal_rank_total / total
    run.average_latency_ms = latency_total / total
    session.add_all(items)
    run.items = items
    session.commit()
    return to_run_response(run)


def list_evaluation_runs(session: Session) -> list[EvaluationRunResponse]:
    runs = session.scalars(
        select(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(20)
    ).all()
    return [to_run_response(run, include_items=False) for run in runs]
