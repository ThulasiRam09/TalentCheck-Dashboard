"""
gemini_service.py
------------------
Wraps all interaction with the Google Gemini API (via the google-genai
SDK). Responsible for sending the analysis prompt and parsing the
model's JSON response into a validated `JobDescriptionAnalysis`.
"""

import json
import logging

from google import genai
from google.genai import types
from pydantic import ValidationError

from app.config import settings
from app.models.response_model import JobDescriptionAnalysis
from app.services.prompt import build_analysis_prompt
from app.utils.helpers import GeminiServiceError

logger = logging.getLogger("jd_analytics.gemini_service")

# A single shared client instance. The genai.Client is lightweight and
# thread-safe to reuse across requests, so we build it once at import
# time using the API key from settings.
_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """
    Lazily construct (and cache) the Gemini client.

    Lazy construction means importing this module never fails even if
    GOOGLE_API_KEY is missing at import time; the actual error is
    raised only when an analysis is attempted, and settings.validate()
    at startup already guards against running the server without a key.
    """
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    return _client


def _strip_markdown_fences(raw_text: str) -> str:
    """
    Defensively strip ```json / ``` fences in case the model wraps its
    output despite instructions not to. Returns the cleaned string.
    """
    text = raw_text.strip()
    if text.startswith("```"):
        # Remove the opening fence (optionally with a language tag).
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1:]
        # Remove a trailing fence if present.
        if text.endswith("```"):
            text = text[: -3]
    return text.strip()


async def analyze_job_description(job_description_text: str) -> JobDescriptionAnalysis:
    """
    Send the extracted Job Description text to Gemini 2.5 Flash and
    parse the structured JSON response.

    Args:
        job_description_text: Raw text extracted from the uploaded file.

    Returns:
        A validated JobDescriptionAnalysis instance.

    Raises:
        GeminiServiceError: if the API call fails, or the response
            cannot be parsed/validated as the expected JSON shape.
    """
    client = _get_client()
    prompt = build_analysis_prompt(job_description_text)

    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                # Ask Gemini to constrain output to valid JSON matching
                # our Pydantic schema directly. This is the most
                # reliable way to get clean structured output from the
                # google-genai SDK.
                response_mime_type="application/json",
                response_schema=JobDescriptionAnalysis,
                temperature=0.2,
            ),
        )
    except Exception as exc:
        logger.exception("Gemini API call failed")
        raise GeminiServiceError(f"Gemini API request failed: {exc}") from exc

    # Prefer the SDK's already-parsed object if available.
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, JobDescriptionAnalysis):
        return parsed

    # Fall back to manually parsing response.text (covers SDK versions
    # or edge cases where `.parsed` isn't populated).
    raw_text = getattr(response, "text", None)
    if not raw_text:
        raise GeminiServiceError("Gemini returned an empty response.")

    cleaned_text = _strip_markdown_fences(raw_text)

    try:
        data = json.loads(cleaned_text)
    except json.JSONDecodeError as exc:
        logger.error("Failed to decode Gemini JSON response: %s", cleaned_text[:500])
        raise GeminiServiceError(
            f"Gemini response was not valid JSON: {exc}"
        ) from exc

    try:
        return JobDescriptionAnalysis(**data)
    except ValidationError as exc:
        logger.error("Gemini JSON failed schema validation: %s", exc)
        raise GeminiServiceError(
            f"Gemini response did not match the expected schema: {exc}"
        ) from exc
