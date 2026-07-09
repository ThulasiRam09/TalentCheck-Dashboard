"""
file_loader.py
--------------
Handles all file I/O for the backend.

Responsibilities:
  - Load all JD files from the /data/jds/ directory at startup
  - Provide cached parsed JDs so they aren't re-parsed on every request
  - Validate file types before parsing

Cache strategy:
  - JDs are parsed once at startup and stored in memory (they rarely change).
  - Resumes are parsed per request (user uploads fresh resumes).
"""

import logging
from pathlib import Path
from functools import lru_cache
from typing import Optional

from services.schemas import ParsedJD

logger = logging.getLogger(__name__)

# Absolute path to the data directories
BASE_DIR = Path(__file__).resolve().parent.parent  # → backend/
JD_DIR = BASE_DIR / "data" / "jds"
RESUME_DIR = BASE_DIR / "data" / "resumes"

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}


def validate_extension(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def load_all_jd_files() -> list[tuple[bytes, str]]:
    """
    Scan the JD directory and return a list of (file_bytes, filename) tuples.
    """
    if not JD_DIR.exists():
        logger.error("JD directory not found: %s", JD_DIR)
        return []

    jd_files = []
    for filepath in sorted(JD_DIR.iterdir()):
        if filepath.suffix.lower() in ALLOWED_EXTENSIONS:
            try:
                with open(filepath, "rb") as f:
                    jd_files.append((f.read(), filepath.name))
                logger.info("Loaded JD file: %s", filepath.name)
            except Exception as e:
                logger.warning("Could not load JD file %s: %s", filepath.name, e)

    return jd_files


def load_all_resume_files() -> list[tuple[bytes, str]]:
    """
    Scan the resumes directory and return a list of (file_bytes, filename) tuples.
    Used for batch processing during demo.
    """
    if not RESUME_DIR.exists():
        logger.warning("Resume directory not found: %s", RESUME_DIR)
        return []

    resume_files = []
    for filepath in sorted(RESUME_DIR.iterdir()):
        if filepath.suffix.lower() in ALLOWED_EXTENSIONS:
            try:
                with open(filepath, "rb") as f:
                    resume_files.append((f.read(), filepath.name))
                logger.info("Loaded resume file: %s", filepath.name)
            except Exception as e:
                logger.warning("Could not load resume file %s: %s", filepath.name, e)

    return resume_files
