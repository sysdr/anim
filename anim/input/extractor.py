"""Text extraction from various input sources."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from anim.blueprint.schema import Blueprint, Element, Scene, SceneType


def extract_text_from_pdf(path: str | Path) -> str:
    """Extract text from PDF. Requires pypdf or PyPDF2."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    try:
        from pypdf import PdfReader

        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError:
        raise ImportError("pypdf required for PDF extraction. Install with: pip install pypdf") from None


def extract_text_from_url(url: str) -> str:
    """Extract text from URL (web page)."""
    parsed = urlparse(url)
    if not parsed.scheme or parsed.scheme not in ("http", "https"):
        raise ValueError(f"Invalid URL scheme: {url}")

    try:
        import urllib.request

        with urllib.request.urlopen(url, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            return soup.get_text(separator="\n", strip=True)
        except ImportError:
            import re

            text = re.sub(r"<[^>]+>", " ", html)
            return re.sub(r"\s+", " ", text).strip()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch URL: {e}") from e


def extract_text(source: str | Path) -> str:
    """Extract text from PDF path, URL, or return as-is if plain text."""
    s = str(source).strip()
    if s.startswith(("http://", "https://")):
        return extract_text_from_url(s)
    path = Path(source)
    if path.suffix.lower() == ".pdf":
        return extract_text_from_pdf(path)
    return s
