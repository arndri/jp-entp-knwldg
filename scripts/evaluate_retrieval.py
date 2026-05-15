from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.retrieval import retrieve


@dataclass(frozen=True)
class EvalQuestion:
    id: str
    question: str
    expected_document: str
    expected_pages: set[int]


def load_questions(path: Path) -> list[EvalQuestion]:
    questions: list[EvalQuestion] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        questions.append(
            EvalQuestion(
                id=raw["id"],
                question=raw["question"],
                expected_document=raw["expected_document"],
                expected_pages=set(raw["expected_pages"]),
            )
        )
    return questions


def evaluate(path: Path, top_k: int, access_levels: list[str]) -> dict[str, float | int]:
    questions = load_questions(path)
    if not questions:
        raise ValueError("No evaluation questions found.")

    hits_at_k = 0
    reciprocal_rank_total = 0.0

    for item in questions:
        citations = retrieve(item.question, access_levels)[:top_k]
        rank = next(
            (
                index
                for index, citation in enumerate(citations, start=1)
                if citation.title == item.expected_document
                and citation.page_number in item.expected_pages
            ),
            None,
        )
        if rank is not None:
            hits_at_k += 1
            reciprocal_rank_total += 1 / rank

    total = len(questions)
    return {
        "questions": total,
        f"recall_at_{top_k}": hits_at_k / total,
        "mrr": reciprocal_rank_total / total,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval against a gold JSONL set.")
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--access-level", action="append", dest="access_levels", default=["public"])
    args = parser.parse_args()

    try:
        results = evaluate(args.questions, args.top_k, args.access_levels)
    except Exception as exc:
        raise SystemExit(
            "Retrieval evaluation failed. Ensure Qdrant is running, the target documents are indexed, "
            f"and the evaluation set matches the indexed corpus. Original error: {exc}"
        ) from exc

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
