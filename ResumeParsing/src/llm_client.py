import os

import google.generativeai as genai
from dotenv import load_dotenv


load_dotenv()


def call_gemini(prompt: str) -> str:
    """Send prompt to Gemini and return raw text response."""
    api_key = os.getenv("GOOGLE_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is missing. Create a .env file from .env.example."
        )

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.1,
            "response_mime_type": "application/json",
        },
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    return response.text
