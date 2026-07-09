"""
helpers.py
----------
Small shared utilities: custom exceptions and file-handling helpers
used across routers/services. Keeping exceptions here (rather than in
each service module) avoids circular imports since multiple layers
need to raise/catch the same exception types.
"""

import os
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import settings


# --------------------------------------------------------------------------
# Custom exceptions
#
# Each maps to a distinct failure mode requested in the spec:
# invalid file, empty file, extraction failure, gemini failure.
# Routers catch these and translate them into clean HTTP error responses.
# --------------------------------------------------------------------------

class InvalidFileError(Exception):
    """Raised when the uploaded file type/extension/size is not allowed."""


class EmptyFileError(Exception):
    """Raised when the uploaded file has no content, or no extractable text."""


class ExtractionError(Exception):
    """Raised when text extraction from PDF/DOCX fails."""


class GeminiServiceError(Exception):
    """Raised when the Gemini API call fails or returns an unusable response."""


def validate_upload(file: UploadFile, contents: bytes) -> None:
    """
    Validate an uploaded file's extension, content-type, and size.

    Raises:
        InvalidFileError: if the extension/content-type is not allowed,
            or the file exceeds the maximum allowed size.
        EmptyFileError: if the file has zero bytes.
    """
    if not file.filename:
        raise InvalidFileError("Uploaded file is missing a filename.")

    extension = Path(file.filename).suffix.lower()
    if extension not in settings.ALLOWED_EXTENSIONS:
        raise InvalidFileError(
            f"Unsupported file extension '{extension}'. "
            f"Allowed types: {', '.join(sorted(settings.ALLOWED_EXTENSIONS))}."
        )

    # content_type is client-supplied and not fully trustworthy, but we
    # check it as a first line of defense in addition to the extension.
    if file.content_type not in settings.ALLOWED_CONTENT_TYPES:
        raise InvalidFileError(
            f"Unsupported content type '{file.content_type}'. "
            f"Expected PDF or DOCX."
        )

    if len(contents) == 0:
        raise EmptyFileError("Uploaded file is empty.")

    if len(contents) > settings.MAX_FILE_SIZE_BYTES:
        raise InvalidFileError(
            f"File exceeds the maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB."
        )


def save_temp_file(contents: bytes, original_filename: str) -> str:
    """
    Persist uploaded bytes to the uploads/ directory under a unique
    name (to avoid collisions) and return the path to the saved file.

    The caller is responsible for deleting this file once processing
    is complete (see delete_temp_file), so uploads/ does not grow
    unbounded during normal operation.
    """
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    extension = Path(original_filename).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as f:
        f.write(contents)

    return file_path


def delete_temp_file(file_path: str) -> None:
    """Best-effort cleanup of a temporary uploaded file."""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except OSError:
        # Cleanup failures should never crash the request; the file can
        # be garbage-collected later or manually if needed.
        pass
