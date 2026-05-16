import os
from pathlib import Path
from typing import Protocol

from app.core.config import get_settings
from app.services.pdf import count_pdf_pages, extract_pdf_pages


class PageExtractor(Protocol):
    def extract_pages(self, path: Path) -> list[tuple[int, str]]:
        ...


class PyPdfExtractor:
    def extract_pages(self, path: Path) -> list[tuple[int, str]]:
        return extract_pdf_pages(path)


class DoclingExtractor:
    def __init__(
        self,
        do_ocr: bool = False,
        device: str = "cpu",
        hf_token: str = "",
        fallback_to_pypdf: bool = True,
        layout_batch_size: int = 1,
        ocr_batch_size: int = 1,
        table_batch_size: int = 1,
        max_pages: int = 15,
    ) -> None:
        self.do_ocr = do_ocr
        self.device = device
        self.hf_token = hf_token
        self.fallback_to_pypdf = fallback_to_pypdf
        self.layout_batch_size = layout_batch_size
        self.ocr_batch_size = ocr_batch_size
        self.table_batch_size = table_batch_size
        self.max_pages = max_pages

    def extract_pages(self, path: Path) -> list[tuple[int, str]]:
        if count_pdf_pages(path) > self.max_pages:
            return extract_pdf_pages(path)

        from docling.datamodel.accelerator_options import AcceleratorOptions
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption

        if self.hf_token:
            os.environ.setdefault("HF_TOKEN", self.hf_token)

        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = self.do_ocr
        pipeline_options.accelerator_options = AcceleratorOptions(device=self.device)
        pipeline_options.layout_batch_size = self.layout_batch_size
        pipeline_options.ocr_batch_size = self.ocr_batch_size
        pipeline_options.table_batch_size = self.table_batch_size
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
            }
        )
        document = converter.convert(path).document

        pages: dict[int, str] = {}
        for page_no in sorted(document.pages):
            text = document.export_to_text(page_no=page_no, traverse_pictures=True)
            normalized = " ".join(text.split())
            if normalized:
                pages[page_no] = normalized

        if self.fallback_to_pypdf:
            for page_no, text in extract_pdf_pages(path):
                pages.setdefault(page_no, text)

        return sorted(pages.items())


def get_page_extractor() -> PageExtractor:
    settings = get_settings()
    match settings.document_extractor.lower():
        case "pypdf":
            return PyPdfExtractor()
        case "docling":
            return DoclingExtractor(
                do_ocr=settings.docling_do_ocr,
                device=settings.docling_device,
                hf_token=settings.hf_token,
                fallback_to_pypdf=settings.docling_fallback_to_pypdf,
                layout_batch_size=settings.docling_layout_batch_size,
                ocr_batch_size=settings.docling_ocr_batch_size,
                table_batch_size=settings.docling_table_batch_size,
                max_pages=settings.docling_max_pages,
            )
        case extractor:
            raise ValueError(f"Unsupported document extractor: {extractor}")
