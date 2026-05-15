from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Chunk:
    page_number: int
    text: str


SENTENCE_BOUNDARY = re.compile(r"(?<=[。！？.!?])")


def split_sentences(text: str) -> list[str]:
    sentences = [segment.strip() for segment in SENTENCE_BOUNDARY.split(text) if segment.strip()]
    return sentences or ([text.strip()] if text.strip() else [])


def split_long_sentence(sentence: str, chunk_size: int) -> list[str]:
    return [
        sentence[start : start + chunk_size].strip()
        for start in range(0, len(sentence), chunk_size)
        if sentence[start : start + chunk_size].strip()
    ]


def tail_overlap_sentences(sentences: list[str], overlap: int) -> list[str]:
    selected: list[str] = []
    current_length = 0

    for sentence in reversed(sentences):
        proposed_length = current_length + len(sentence)
        if proposed_length > overlap:
            break
        selected.append(sentence)
        current_length = proposed_length

    return list(reversed(selected))


def chunk_pages(
    pages: list[tuple[int, str]],
    chunk_size: int,
    overlap: int,
) -> list[Chunk]:
    chunks: list[Chunk] = []

    for page_number, text in pages:
        sentences: list[str] = []
        for sentence in split_sentences(text):
            if len(sentence) > chunk_size:
                sentences.extend(split_long_sentence(sentence, chunk_size))
            else:
                sentences.append(sentence)

        current_sentences: list[str] = []
        current_length = 0

        for sentence in sentences:
            separator_length = 1 if current_sentences else 0
            proposed_length = current_length + separator_length + len(sentence)

            if current_sentences and proposed_length > chunk_size:
                chunks.append(Chunk(page_number=page_number, text=" ".join(current_sentences)))
                current_sentences = tail_overlap_sentences(current_sentences, overlap)
                current_length = len(" ".join(current_sentences))
                separator_length = 1 if current_sentences else 0

            current_sentences.append(sentence)
            current_length += separator_length + len(sentence)

        if current_sentences:
            chunks.append(Chunk(page_number=page_number, text=" ".join(current_sentences)))

    return chunks
