from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    page_number: int
    text: str


def chunk_pages(
    pages: list[tuple[int, str]],
    chunk_size: int,
    overlap: int,
) -> list[Chunk]:
    chunks: list[Chunk] = []

    for page_number, text in pages:
        start = 0
        text_len = len(text)
        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(Chunk(page_number=page_number, text=chunk_text))
            if end >= text_len:
                break
            start = max(0, end - overlap)

    return chunks

