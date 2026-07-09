import json
import re
from pathlib import Path
from typing import Any

from src.models import ResumeParseResult


def extract_json_from_text(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No valid JSON found in LLM response.")

    return json.loads(match.group(0))


def ensure_list(value):
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def normalize_string_list(value):
    items = ensure_list(value)
    result = []

    for item in items:
        if isinstance(item, str):
            result.append(item)

        elif isinstance(item, dict):
            name = (
                item.get("name")
                or item.get("title")
                or item.get("certification")
                or item.get("role")
                or item.get("description")
                or ""
            )
            if name:
                result.append(str(name))

    return result


def normalize_technologies(value):
    if value is None:
        return []

    if isinstance(value, list):
        return [str(item) for item in value if item]

    if isinstance(value, str):
        return [value]

    return []


def normalize_object_list(value, allowed_keys):
    items = ensure_list(value)
    result = []

    for item in items:
        cleaned = {key: "" for key in allowed_keys}

        if isinstance(item, dict):
            for key in allowed_keys:
                cleaned[key] = item.get(key, "")

            if "technologies" in cleaned:
                cleaned["technologies"] = normalize_technologies(cleaned["technologies"])

            result.append(cleaned)

        elif isinstance(item, str):
            first_key = allowed_keys[0]
            cleaned[first_key] = item

            if "technologies" in cleaned:
                cleaned["technologies"] = []

            result.append(cleaned)

    return result


def normalize_skills(value):
    items = ensure_list(value)
    result = []

    valid_categories = {
        "DSA", "COD", "OOD", "APTI", "COMM", "AI",
        "CLOUD", "SQL", "SWE", "SYSD", "NETW", "OS", "OTHER"
    }

    valid_confidence = {"high", "medium", "low"}

    for item in items:
        if isinstance(item, str):
            result.append({
                "skill_name": item,
                "category_code": "OTHER",
                "evidence": item,
                "confidence": "medium"
            })

        elif isinstance(item, dict):
            skill_name = (
                item.get("skill_name")
                or item.get("name")
                or item.get("skill")
                or ""
            )

            category_code = str(
                item.get("category_code")
                or item.get("category")
                or "OTHER"
            ).upper()

            if category_code not in valid_categories:
                category_code = "OTHER"

            confidence = str(item.get("confidence") or "medium").lower()

            if confidence not in valid_confidence:
                confidence = "medium"

            result.append({
                "skill_name": str(skill_name),
                "category_code": category_code,
                "evidence": str(item.get("evidence") or ""),
                "confidence": confidence
            })

    return [skill for skill in result if skill["skill_name"].strip()]


def normalize_resume_json(data: dict[str, Any], source_file: str) -> dict[str, Any]:
    data["source_type"] = "resume"
    data["source_file"] = Path(source_file).name

    data.setdefault("company", "")
    data.setdefault("role", "")

    data.setdefault("name", "")
    data.setdefault("email", "")
    data.setdefault("phone", "")
    data.setdefault("linkedin", "")
    data.setdefault("github", "")

    data["education"] = normalize_object_list(
        data.get("education", []),
        ["institution", "degree", "field", "year", "evidence"]
    )

    data["projects"] = normalize_object_list(
        data.get("projects", []),
        ["name", "description", "technologies", "evidence"]
    )

    data["experience"] = normalize_object_list(
        data.get("experience", []),
        ["organization", "role", "duration", "description", "technologies", "evidence"]
    )

    data["certifications"] = normalize_string_list(data.get("certifications", []))

    data["hackathons"] = normalize_object_list(
        data.get("hackathons", []),
        ["name", "role", "duration", "description", "technologies", "evidence"]
    )

    data["preferred_roles"] = normalize_string_list(data.get("preferred_roles", []))
    data["skills"] = normalize_skills(data.get("skills", []))

    data.setdefault("summary", "")

    return data


def validate_resume_json(data: dict[str, Any], source_file: str) -> dict[str, Any]:
    normalized = normalize_resume_json(data, source_file)
    validated = ResumeParseResult.model_validate(normalized)
    return validated.model_dump()