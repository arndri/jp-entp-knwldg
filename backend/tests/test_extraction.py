from app.services.extraction import DoclingExtractor, PyPdfExtractor, get_page_extractor


def test_get_page_extractor_defaults_to_pypdf(monkeypatch) -> None:
    class FakeSettings:
        document_extractor = "pypdf"
        docling_do_ocr = False
        docling_device = "cpu"
        docling_fallback_to_pypdf = True
        docling_layout_batch_size = 1
        docling_ocr_batch_size = 1
        docling_table_batch_size = 1
        docling_max_pages = 15
        hf_token = ""

    monkeypatch.setattr("app.services.extraction.get_settings", lambda: FakeSettings())

    assert isinstance(get_page_extractor(), PyPdfExtractor)


def test_get_page_extractor_supports_docling(monkeypatch) -> None:
    class FakeSettings:
        document_extractor = "docling"
        docling_do_ocr = True
        docling_device = "cpu"
        docling_fallback_to_pypdf = False
        docling_layout_batch_size = 2
        docling_ocr_batch_size = 3
        docling_table_batch_size = 4
        docling_max_pages = 5
        hf_token = "token"

    monkeypatch.setattr("app.services.extraction.get_settings", lambda: FakeSettings())

    extractor = get_page_extractor()
    assert isinstance(extractor, DoclingExtractor)
    assert extractor.do_ocr is True
    assert extractor.device == "cpu"
    assert extractor.hf_token == "token"
    assert extractor.fallback_to_pypdf is False
    assert extractor.layout_batch_size == 2
    assert extractor.ocr_batch_size == 3
    assert extractor.table_batch_size == 4
    assert extractor.max_pages == 5


def test_get_page_extractor_rejects_unknown_extractor(monkeypatch) -> None:
    class FakeSettings:
        document_extractor = "unknown"
        docling_do_ocr = False
        docling_device = "cpu"
        docling_fallback_to_pypdf = True
        docling_layout_batch_size = 1
        docling_ocr_batch_size = 1
        docling_table_batch_size = 1
        docling_max_pages = 15
        hf_token = ""

    monkeypatch.setattr("app.services.extraction.get_settings", lambda: FakeSettings())

    try:
        get_page_extractor()
    except ValueError as exc:
        assert "Unsupported document extractor" in str(exc)
    else:
        raise AssertionError("Expected unsupported extractor error")


def test_docling_extractor_uses_pypdf_for_large_documents(monkeypatch, tmp_path) -> None:
    path = tmp_path / "large.pdf"
    path.write_text("placeholder")
    extractor = DoclingExtractor(max_pages=10)

    monkeypatch.setattr("app.services.extraction.count_pdf_pages", lambda _: 11)
    monkeypatch.setattr("app.services.extraction.extract_pdf_pages", lambda _: [(1, "fallback")])

    assert extractor.extract_pages(path) == [(1, "fallback")]
