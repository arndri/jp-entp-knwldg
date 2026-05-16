from types import SimpleNamespace

import pytest

from app.schemas.rag import Citation
from app.services import llm


def sample_citations() -> list[Citation]:
    return [
        Citation(
            document_id="doc-1",
            title="sample.pdf",
            page_number=1,
            chunk_id="chunk-1",
            excerpt="Relevant text",
            score=0.9,
        )
    ]


def test_generate_answer_uses_deepseek_configuration(monkeypatch) -> None:
    observed: dict[str, object] = {}

    class FakeCompletions:
        def create(self, **kwargs):
            observed["request"] = kwargs
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="answer"))]
            )

    class FakeClient:
        def __init__(self, **kwargs):
            observed["client"] = kwargs
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr(
        llm,
        "get_settings",
        lambda: SimpleNamespace(
            llm_provider="deepseek",
            deepseek_api_key="secret",
            deepseek_base_url="https://api.deepseek.com",
            deepseek_model="deepseek-v4-flash",
        ),
    )
    monkeypatch.setattr(llm, "OpenAI", FakeClient)

    answer = llm.generate_answer("question", sample_citations())

    assert answer == "answer"
    assert observed["client"] == {
        "api_key": "secret",
        "base_url": "https://api.deepseek.com",
    }
    assert observed["request"]["model"] == "deepseek-v4-flash"


def test_generate_answer_requires_deepseek_key(monkeypatch) -> None:
    monkeypatch.setattr(
        llm,
        "get_settings",
        lambda: SimpleNamespace(
            llm_provider="deepseek",
            deepseek_api_key="",
        ),
    )

    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY is missing"):
        llm.generate_answer("question", sample_citations())
