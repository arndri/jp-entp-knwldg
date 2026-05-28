from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from app.models import utc_now
from app.services.evaluation import load_eval_questions, run_retrieval_evaluation


class FakeSession:
    def __init__(self) -> None:
        self.objects = []

    def add(self, item) -> None:
        self.objects.append(item)

    def add_all(self, items) -> None:
        self.objects.extend(items)

    def flush(self) -> None:
        for item in self.objects:
            if getattr(item, "id", None) is None:
                item.id = str(uuid4())
            if getattr(item, "status", None) is None:
                item.status = "completed"
            if getattr(item, "created_at", None) is None:
                item.created_at = utc_now()
        return None

    def commit(self) -> None:
        return None

    def refresh(self, item) -> None:
        return None


def test_load_eval_questions(tmp_path: Path) -> None:
    path = tmp_path / "questions.jsonl"
    path.write_text(
        '{"id":"q1","question":"hello","expected_document":"sample.pdf","expected_pages":[1,2]}',
        encoding="utf-8",
    )

    questions = load_eval_questions(path)

    assert questions[0].id == "q1"
    assert questions[0].expected_pages == {1, 2}


def test_run_retrieval_evaluation_calculates_metrics(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "questions.jsonl"
    path.write_text(
        "\n".join(
            [
                '{"id":"q1","question":"first","expected_document":"sample.pdf","expected_pages":[1]}',
                '{"id":"q2","question":"second","expected_document":"missing.pdf","expected_pages":[5]}',
            ]
        ),
        encoding="utf-8",
    )

    def fake_retrieve(question, access_levels):
        return [
            SimpleNamespace(title="sample.pdf", page_number=1),
            SimpleNamespace(title="other.pdf", page_number=2),
        ]

    monkeypatch.setattr("app.services.evaluation.retrieve", fake_retrieve)
    session = FakeSession()

    response = run_retrieval_evaluation(
        session,
        SimpleNamespace(
            name="test",
            question_set_path=str(path),
            top_k=5,
            access_levels=["public"],
        ),
        SimpleNamespace(id="admin-1"),
    )

    assert response.question_count == 2
    assert response.hit_count == 1
    assert response.recall_at_k == 0.5
    assert response.mrr == 0.5
    assert response.items[0].hit is True
    assert response.items[1].hit is False
