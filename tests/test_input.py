"""Tests for input pipeline."""

from pathlib import Path
from unittest.mock import patch

import pytest

from anim.input.extractor import extract_text, extract_text_from_pdf, extract_text_from_url


class TestExtractText:
    """Tests for extract_text."""

    def test_plain_text(self):
        assert extract_text("Hello world") == "Hello world"

    def test_url(self):
        with patch("anim.input.extractor.extract_text_from_url") as mock:
            mock.return_value = "Web content"
            result = extract_text("https://example.com")
            mock.assert_called_once_with("https://example.com")
            assert result == "Web content"

    def test_pdf_path(self, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        with patch("anim.input.extractor.extract_text_from_pdf") as mock:
            mock.return_value = "PDF content"
            result = extract_text(pdf_path)
            mock.assert_called_once()
            assert result == "PDF content"


class TestExtractTextFromPdf:
    """Tests for extract_text_from_pdf."""

    def test_missing_file_raises(self, tmp_path):
        missing = tmp_path / "nonexistent.pdf"
        with pytest.raises(FileNotFoundError):
            extract_text_from_pdf(missing)

    def test_with_pypdf(self, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 minimal\n")
        with patch("pypdf.PdfReader") as mock_reader:
            mock_page = type("Page", (), {"extract_text": lambda self: "Page text"})()
            mock_reader.return_value.pages = [mock_page]
            result = extract_text_from_pdf(pdf_path)
            assert "Page text" in result or result == "Page text"
