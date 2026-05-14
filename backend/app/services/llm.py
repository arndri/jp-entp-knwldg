from openai import OpenAI

from app.core.config import get_settings
from app.schemas.rag import Citation


def build_prompt(question: str, citations: list[Citation]) -> str:
    context = "\n\n".join(
        f"[{index}] Source: {citation.title}, page {citation.page_number}\n{citation.excerpt}"
        for index, citation in enumerate(citations, start=1)
    )
    return f"""You are a Japanese enterprise knowledge assistant.
Answer only from the provided context. If the context is insufficient, say that the documents do not contain enough information.
Answer in the same language as the user's question when possible.
Include concise source markers like [1] or [2] where relevant.

Context:
{context}

Question:
{question}
"""


def generate_answer(question: str, citations: list[Citation]) -> str:
    settings = get_settings()
    if settings.llm_provider != "openai":
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is missing.")

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": "You answer enterprise document questions with citations and avoid unsupported claims.",
            },
            {"role": "user", "content": build_prompt(question, citations)},
        ],
    )
    return response.choices[0].message.content or ""

