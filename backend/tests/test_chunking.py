from app.services.chunking import (
    chunk_pages,
    split_long_sentence,
    split_sentences,
    tail_overlap_sentences,
)


def test_split_sentences_handles_japanese_and_english_boundaries() -> None:
    text = "第一文です。第二文です！Third sentence. Fourth sentence?"

    assert split_sentences(text) == [
        "第一文です。",
        "第二文です！",
        "Third sentence.",
        "Fourth sentence?",
    ]


def test_split_long_sentence_falls_back_to_hard_chunks() -> None:
    sentence = "abcdefghij"

    assert split_long_sentence(sentence, chunk_size=4) == ["abcd", "efgh", "ij"]


def test_tail_overlap_keeps_only_complete_sentences_within_budget() -> None:
    sentences = ["aaaa", "bbbb", "cc"]

    assert tail_overlap_sentences(sentences, overlap=6) == ["bbbb", "cc"]


def test_chunk_pages_preserves_sentence_boundaries_and_overlap() -> None:
    pages = [(1, "第一文です。第二文です。Third sentence. Fourth sentence!")]

    chunks = chunk_pages(pages, chunk_size=18, overlap=8)

    assert [chunk.text for chunk in chunks] == [
        "第一文です。 第二文です。",
        "第二文です。 Third sentence.",
        "Fourth sentence!",
    ]
    assert [chunk.page_number for chunk in chunks] == [1, 1, 1]


def test_chunk_pages_never_crosses_page_boundaries() -> None:
    pages = [
        (1, "Page one sentence."),
        (2, "Page two sentence."),
    ]

    chunks = chunk_pages(pages, chunk_size=100, overlap=20)

    assert [chunk.page_number for chunk in chunks] == [1, 2]
    assert [chunk.text for chunk in chunks] == ["Page one sentence.", "Page two sentence."]

