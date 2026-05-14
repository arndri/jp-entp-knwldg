from pathlib import Path

from pypdf import PdfReader


def extract_pdf_pages(path: Path) -> list[tuple[int, str]]:
    reader = PdfReader(str(path))
    pages: list[tuple[int, str]] = []

    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = " ".join(text.split())
        if text:
            pages.append((index, text))

    return pages

