"""
upload.py
---------
API routes for uploading a Job Description file and returning
Gemini-generated structured analytics about it.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.models.response_model import AnalyzeResponse
from app.services.docx_reader import extract_text_from_docx
from app.services.gemini_service import analyze_job_description
from app.services.pdf_reader import extract_text_from_pdf
from app.utils.helpers import (
    EmptyFileError,
    ExtractionError,
    GeminiServiceError,
    InvalidFileError,
    delete_temp_file,
    save_temp_file,
    validate_upload,
)

logger = logging.getLogger("jd_analytics.upload")

router = APIRouter(tags=["Analysis"])


def _extract_text(file_path: str, extension: str) -> str:
    """
    Dispatch to the correct extraction service based on file extension.

    Kept as a small standalone function (rather than inline in the
    route) so it's independently testable and acts as a simple form
    of dependency injection for the extraction step.
    """
    if extension == ".pdf":
        return extract_text_from_pdf(file_path)
    if extension == ".docx":
        return extract_text_from_docx(file_path)
    # Should be unreachable because validate_upload() already filters
    # extensions, but guarded here for safety/defense-in-depth.
    raise InvalidFileError(f"Unsupported file extension '{extension}'.")


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze a Job Description file (PDF or DOCX)",
    description=(
        "Upload a Job Description as a PDF or DOCX file. The backend "
        "extracts the text, sends it to Google Gemini 2.5 Flash, and "
        "returns structured analytics (skills, responsibilities, "
        "seniority, etc.) as JSON."
    ),
)
async def analyze_job_description_endpoint(
    file: UploadFile = File(..., description="The Job Description file (PDF or DOCX)."),
) -> AnalyzeResponse:
    """
    Main endpoint: upload -> validate -> extract text -> Gemini -> JSON.
    """
    temp_file_path: str | None = None

    try:
        # Read the full upload into memory. Size validation happens in
        # validate_upload() right after, using the byte length here.
        contents = await file.read()

        # Step 1: Validate file type, content-type, and size.
        validate_upload(file, contents)

        # Step 2: Persist to disk temporarily (extraction libraries
        # work off file paths).
        temp_file_path = save_temp_file(contents, file.filename)
        extension = Path(file.filename).suffix.lower()

        # Step 3: Extract raw text from the PDF/DOCX.
        extracted_text = _extract_text(temp_file_path, extension)

        # Step 4: Send extracted text to Gemini and get structured analytics.
        analysis = await analyze_job_description(extracted_text)

        return AnalyzeResponse(
            success=True,
            filename=file.filename,
            analysis=analysis,
        )

    except InvalidFileError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    except EmptyFileError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    except ExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    except GeminiServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    except HTTPException:
        # Re-raise already-formed HTTP exceptions unchanged.
        raise

    except Exception as exc:
        # Catch-all for truly unexpected errors so the API never leaks
        # a raw stack trace to the client.
        logger.exception("Unexpected error while analyzing job description")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {exc}",
        ) from exc

    finally:
        # Always clean up the temp file, success or failure.
        if temp_file_path:
            delete_temp_file(temp_file_path)
        await file.close()
