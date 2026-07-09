from pathlib import Path

from docx import Document
from pypdf import PdfReader


def extract_pdf_text(file_path: str) -> str:
    """Extract readable text from a PDF resume."""
    reader = PdfReader(file_path)
    pages = []

    for page in reader.pages:
        text = page.extract_text()
        if text and text.strip():
            pages.append(text.strip())

    return "\n\n".join(pages)


def extract_docx_text(file_path: str) -> str:
    """Extract readable text from a DOCX resume."""
    document = Document(file_path)
    paragraphs = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs)


def extract_text(file_path: str) -> str:
    """Route the uploaded file to the correct extractor based on extension."""
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".pdf":
        text = extract_pdf_text(file_path)
    elif extension == ".docx":
        text = extract_docx_text(file_path)
    else:
        raise ValueError("Unsupported file type. Only PDF and DOCX are supported.")

    if not text.strip():
        raise ValueError(
            "No readable text was extracted. The resume may be scanned/image-based."
        )

    return text
