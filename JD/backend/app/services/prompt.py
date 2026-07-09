"""
prompt.py
---------
Prompt engineering for the Gemini analysis request.

Keeping the prompt in its own module makes it easy to iterate on
wording without touching the API call logic in gemini_service.py.
"""

# JSON schema description shown to the model. Kept in plain text
# (rather than passing a jsonschema dict) so we can also enforce it
# via Gemini's structured output `response_schema` config, while still
# giving the model an explicit, readable contract in the prompt itself.
RESPONSE_JSON_SHAPE = """{
  "summary": "string",
  "skills": ["string"],
  "responsibilities": ["string"],
  "experience": "string",
  "education": "string",
  "technologies": ["string"],
  "soft_skills": ["string"],
  "keywords": ["string"],
  "seniority": "string",
  "job_type": "string",
  "location": "string"
}"""


def build_analysis_prompt(job_description_text: str) -> str:
    """
    Build the full prompt sent to Gemini for a given Job Description.

    The prompt instructs the model to:
      - Act as an expert HR / technical recruiter analyst.
      - Extract 11 specific fields from the JD.
      - Return ONLY raw JSON, matching an exact shape, with no
        markdown fences, commentary, or extra text.

    Args:
        job_description_text: Raw text extracted from the uploaded
            PDF/DOCX Job Description.

    Returns:
        The complete prompt string ready to send to Gemini.
    """
    return f"""You are an expert technical recruiter and HR analyst.

Analyze the following Job Description text and extract structured
analytics from it. Be accurate, concise, and base every field ONLY
on information present in (or reasonably inferable from) the text.
If a field cannot be determined, use an empty string "" for text
fields or an empty array [] for list fields — never invent facts.

Extract exactly the following fields:
1. summary - A concise 2-4 sentence summary of the role.
2. skills - Hard/technical skills explicitly required or preferred.
3. responsibilities - Key day-to-day duties and responsibilities.
4. experience - Required years and/or level of experience (e.g. "3-5 years").
5. education - Required or preferred educational qualifications.
6. technologies - Specific tools, frameworks, languages, platforms mentioned.
7. soft_skills - Interpersonal/behavioral skills (e.g. communication, leadership).
8. keywords - Notable ATS-style keywords/phrases that summarize the JD.
9. seniority - Seniority level (e.g. "Intern", "Junior", "Mid", "Senior", "Lead", "Principal").
10. job_type - Employment type (e.g. "Full-time", "Part-time", "Contract", "Internship", "Remote", "Hybrid").
11. location - Job location if mentioned (city/country/remote); "" if not stated.

Return ONLY a single valid JSON object matching EXACTLY this shape,
with no additional keys and no missing keys:

{RESPONSE_JSON_SHAPE}

STRICT OUTPUT RULES:
- Output raw JSON only.
- Do NOT wrap the JSON in markdown code fences (no ```json).
- Do NOT include any explanation, preamble, or commentary before or after the JSON.
- Do NOT include trailing commas.
- All string values must be valid JSON strings (properly escaped).

--- JOB DESCRIPTION START ---
{job_description_text}
--- JOB DESCRIPTION END ---
"""
