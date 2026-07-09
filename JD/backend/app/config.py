"""
config.py
---------
Centralized application configuration.

Loads environment variables from a .env file (via python-dotenv) and
exposes them as a single, importable `settings` object so the rest of
the application never touches os.environ directly.
"""

import os
from dotenv import load_dotenv

# Load variables from a .env file in the backend/ root into the process
# environment. This is a no-op if the file does not exist, which keeps
# things safe in production environments where env vars are injected
# by the platform instead of a .env file.
load_dotenv()


class Settings:
    """
    Simple settings container.

    Kept as a plain class (rather than pydantic-settings) to minimize
    dependencies, but structured so it is trivial to swap for
    pydantic.BaseSettings later if the project grows.
    """

    # --- Google Gemini ---
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # --- CORS ---
    # Frontend dev server (Vite default port).
    ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]

    # --- Upload constraints ---
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

    ALLOWED_CONTENT_TYPES: set[str] = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    ALLOWED_EXTENSIONS: set[str] = {".pdf", ".docx"}

    # --- Uploads directory ---
    # Files are briefly written here for processing (see utils/helpers.py).
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")

    def validate(self) -> None:
        """
        Fail fast on startup if required configuration is missing.
        Called explicitly from main.py's startup event rather than at
        import time, so importing config.py never has side effects
        that crash test collection, etc.
        """
        if not self.GOOGLE_API_KEY:
            raise RuntimeError(
                "GOOGLE_API_KEY is not set. Copy .env.example to .env and "
                "add your Google Gemini API key before starting the server."
            )


# Single shared settings instance used throughout the app.
settings = Settings()
