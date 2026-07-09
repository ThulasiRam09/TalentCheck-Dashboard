RADIX_CATEGORIES = """
Use only these RADIX category codes:

COD    = Coding, programming languages, frameworks, APIs
DSA    = Data structures and algorithms
OOD    = Object-oriented programming and design
APTI   = Aptitude, logical reasoning, analytical thinking
COMM   = Communication, teamwork, documentation, presentation
AI     = AI, ML, NLP, GenAI, data science
CLOUD  = Cloud, DevOps, AWS, Azure, GCP, Docker, Kubernetes
SQL    = SQL, databases, data modeling
SWE    = Software engineering, Git, testing, CI/CD, debugging, SDLC
SYSD   = System design, architecture, scalability
NETW   = Networking, HTTP, TCP/IP, DNS, protocols
OS     = Operating systems, Linux, shell scripting
OTHER  = Relevant skill that does not fit above
"""


def build_resume_prompt(resume_text: str, source_file: str) -> str:
    return f"""
You are a resume parser for the RADIX Talent Match Hackathon.

Extract structured candidate information from the resume.

{RADIX_CATEGORIES}

Rules:
1. Return ONLY valid JSON.
2. Do NOT use markdown.
3. Do NOT add explanation outside JSON.
4. Do NOT invent missing information.
5. If something is missing, use an empty string or empty list.
6. Every skill must map to one RADIX category code.
7. confidence must be one of: high, medium, low.

Return JSON exactly in this format:

{{
  "source_type": "resume",
  "source_file": "{source_file}",
  "company": "",
  "role": "",

  "name": "",
  "email": "",
  "phone": "",
  "linkedin": "",
  "github": "",

  "education": [
    {{
      "institution": "",
      "degree": "",
      "field": "",
      "year": "",
      "evidence": ""
    }}
  ],

  "projects": [
    {{
      "name": "",
      "description": "",
      "technologies": [],
      "evidence": ""
    }}
  ],

  "experience": [
    {{
      "organization": "",
      "role": "",
      "duration": "",
      "description": "",
      "technologies": [],
      "evidence": ""
    }}
  ],

  "certifications": [],
  "hackathons": [],
  "preferred_roles": [],

  "skills": [
    {{
      "skill_name": "",
      "category_code": "",
      "evidence": "",
      "confidence": ""
    }}
  ],

  "summary": ""
}}

Resume text:
--------------------
{resume_text}
--------------------
"""