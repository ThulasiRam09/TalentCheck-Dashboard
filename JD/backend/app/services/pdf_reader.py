"""
pdf_reader.py
-------------
Extracts plain text from PDF files using PyMuPDF (fitz).
"""

import fitz  # PyMuPDF

from app.utils.helpers import ExtractionError, EmptyFileError


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract and return all text content from a PDF file.

    Args:
        file_path: Path to the PDF file on disk.

    Returns:
        The extracted text, stripped of leading/trailing whitespace.

    Raises:
        ExtractionError: if the PDF cannot be opened or parsed.
        EmptyFileError: if the PDF contains no extractable text
            (e.g. a scanned image-only PDF with no OCR layer).
    """
    try:
        document = fitz.open(file_path)
    except Exception as exc:
        # Covers corrupted files, password-protected PDFs that fitz
        # can't open, unsupported formats, etc.
        raise ExtractionError(f"Failed to open PDF file: {exc}") from exc

    try:
        text_chunks: list[str] = []
        for page in document:
            page_text = page.get_text("text")
            if page_text:
                text_chunks.append(page_text)
    except Exception as exc:
        raise ExtractionError(f"Failed to extract text from PDF: {exc}") from exc
    finally:
        document.close()

    full_text = "\n".join(text_chunks).strip()

    if not full_text:
        raise EmptyFileError(
            "No extractable text was found in the PDF. "
            "It may be a scanned/image-only document."
        )

    return full_text
