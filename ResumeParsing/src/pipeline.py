import argparse
import json
from pathlib import Path

from src.llm_client import call_gemini
from src.prompt import build_resume_prompt
from src.text_extractor import extract_text
from src.utils import save_json, save_text
from src.validator import extract_json_from_text, validate_resume_json


def parse_resume_pipeline(file_path: str) -> dict:
    """Full pipeline: file -> text -> LLM -> validated JSON -> saved output."""
    source_path = Path(file_path)

    raw_text = extract_text(str(source_path))
    text_output_path = save_text(
        raw_text,
        Path("output/extracted_text"),
        source_path.name,
    )

    prompt = build_resume_prompt(raw_text, source_path.name)
    llm_response = call_gemini(prompt)

    parsed = extract_json_from_text(llm_response)
    validated_json = validate_resume_json(parsed, source_path.name)

    json_output_path = save_json(
        validated_json,
        Path("output/parsed_json"),
        source_path.name,
    )

    return {
        "raw_text": raw_text,
        "parsed_json": validated_json,
        "text_output_path": str(text_output_path),
        "json_output_path": str(json_output_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse a resume into RADIX JSON.")
    parser.add_argument("file_path", help="Path to PDF or DOCX resume")
    args = parser.parse_args()

    result = parse_resume_pipeline(args.file_path)
    print(json.dumps(result["parsed_json"], indent=2, ensure_ascii=False))
    print(f"\nSaved JSON to: {result['json_output_path']}")


if __name__ == "__main__":
    main()
