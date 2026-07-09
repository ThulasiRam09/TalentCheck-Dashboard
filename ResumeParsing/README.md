# Resume Parser - RADIX Talent Match Hackathon

This module handles **Role 2: Resume Parsing**.

It accepts a resume in PDF or DOCX format, extracts raw text, sends it to Gemini, and saves a structured JSON output that other modules can use.

## What it does

1. Upload resume
2. Extract text from PDF/DOCX
3. Ask LLM to identify:
   - name
   - email
   - phone
   - education
   - experience
   - projects
   - skills
4. Map skills to RADIX skill categories
5. Save valid JSON to `output/parsed_json/`

## RADIX Categories

- COD: Coding
- DSA: Data Structures and Algorithms
- OOD: Object-Oriented Design
- APTI: Aptitude
- COMM: Communication
- AI: Artificial Intelligence
- CLOUD: Cloud
- SQL: SQL / Databases
- SWE: Software Engineering
- SYSD: System Design
- NETW: Networking
- OS: Operating Systems
- OTHER: Other

## Setup

```bash
pip install -r requirements.txt
```

Create `.env`:

```bash
cp .env.example .env
```

Add your Gemini API key:

```env
GOOGLE_API_KEY=your_key_here
```

## Run the app

```bash
streamlit run app.py
```

## Run from terminal

```bash
python -m src.pipeline input/resumes/sample_resume.pdf
```

## Output Format

The final JSON follows the shared data contract:

```json
{
  "source_type": "resume",
  "source_file": "resume.pdf",
  "name": "Candidate Name",
  "email": "candidate@email.com",
  "phone": "...",
  "education": [],
  "projects": [],
  "experience": [],
  "skills": [
    {
      "skill_name": "Python",
      "category_code": "COD",
      "evidence": "Built Python automation scripts",
      "confidence": "high"
    }
  ]
}
```

## Important Notes

- Keep the JSON format stable because Profile Builder, Talent Check, and Skill Matching depend on it.
- If Gemini returns invalid JSON, the app tries to recover the JSON block.
- For scanned image resumes, this app may not extract text because OCR is not included.
