import re
from dataclasses import dataclass

from app.core.config import get_settings
from app.schemas.rag import Citation


CONTEXT_REFUSAL = (
    "I could not find relevant authorized document context for this question."
)
POLICY_REFUSAL = (
    "I cannot help with that request. Please ask a question about the authorized documents."
)

INJECTION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bignore\b.{0,40}\b(previous|above|system|developer)\b",
        r"\bdisregard\b.{0,40}\b(previous|above|system|developer)\b",
        r"\breveal\b.{0,40}\b(system prompt|developer prompt|instructions?)\b",
        r"\bshow\b.{0,40}\b(system prompt|developer prompt|hidden instructions?)\b",
        r"\b(system|developer)\s+(message|prompt|instructions?)\b",
        r"\bjailbreak\b",
        r"\bprompt injection\b",
        r"これまでの.*(指示|命令).*無視",
        r"前の.*(指示|命令).*無視",
        r"システム.*(プロンプト|指示).*見せ",
        r"開発者.*(プロンプト|指示).*見せ",
    ]
]


@dataclass(frozen=True)
class GuardrailResult:
    allowed: bool
    reason: str | None = None


def validate_question(question: str) -> GuardrailResult:
    settings = get_settings()
    normalized = question.strip()
    if not normalized:
        return GuardrailResult(False, "Question is empty.")
    if len(normalized) > settings.max_question_chars:
        return GuardrailResult(
            False,
            f"Question is too long. Limit is {settings.max_question_chars} characters.",
        )
    if settings.enable_prompt_injection_filter:
        for pattern in INJECTION_PATTERNS:
            if pattern.search(normalized):
                return GuardrailResult(False, "Prompt-injection pattern detected.")
    return GuardrailResult(True)


def filter_relevant_citations(citations: list[Citation]) -> list[Citation]:
    settings = get_settings()
    return [
        citation
        for citation in citations
        if citation.score is None or citation.score >= settings.min_retrieval_score
    ]


def has_relevant_context(citations: list[Citation]) -> bool:
    return bool(filter_relevant_citations(citations))
