# JD Analytics — Backend

A FastAPI backend that accepts an uploaded Job Description (PDF or DOCX),
extracts its text, sends it to **Google Gemini 2.5 Flash**, and returns
structured JSON analytics (skills, responsibilities, seniority, etc.).

---

## 1. Folder Structure

```
backend/
    app/
        main.py                 # FastAPI app, CORS, global error handlers
        config.py                # Environment/config loading (.env)
        routers/
            upload.py            # POST /analyze endpoint
        services/
            pdf_reader.py         # PDF text extraction (PyMuPDF)
            docx_reader.py        # DOCX text extraction (python-docx)
            gemini_service.py     # Gemini 2.5 Flash API integration
            prompt.py             # Prompt engineering for Gemini
        models/
            response_model.py     # Pydantic response/request models
        utils/
            helpers.py            # Custom exceptions, file validation/IO
    uploads/                    # Temporary storage for uploaded files
    requirements.txt
    .env.example
    README.md
```

---

## 2. Prerequisites

- Python 3.12
- A Google Gemini API key: https://aistudio.google.com/apikey

---

## 3. Installation

### Step 1 — Create and activate a virtual environment

**macOS / Linux**
```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell)**
```powershell
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Configure environment variables

Copy the example env file and add your Gemini API key:

```bash
cp .env.example .env
```

Edit `.env`:

```
GOOGLE_API_KEY=your_actual_api_key_here
```

That's the **only** manual edit required.

---

## 4. Running the Server

```bash
uvicorn app.main:app --reload
```

The server starts at: `http://127.0.0.1:8000`

- Interactive API docs (Swagger UI): **http://127.0.0.1:8000/docs**
- Alternative docs (ReDoc): **http://127.0.0.1:8000/redoc**
- Health check: **http://127.0.0.1:8000/health**

The app validates required configuration (like `GOOGLE_API_KEY`) at
startup and will fail fast with a clear error message if it's missing.

---

## 5. API Usage

### `POST /analyze`

Accepts a single uploaded file (`multipart/form-data`) and returns
structured Job Description analytics.

**Request**

| Field | Type | Description |
|-------|------|-------------|
| `file` | File | PDF or DOCX file, max 10MB |

**Example (cURL)**

```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/job_description.pdf"
```

**Example (JavaScript / fetch, matches the React frontend)**

```javascript
const formData = new FormData();
formData.append("file", fileInput.files[0]);

const response = await fetch("http://localhost:8000/analyze", {
  method: "POST",
  body: formData,
});

const data = await response.json();
console.log(data.analysis);
```

**Success Response — `200 OK`**

```json
{
  "success": true,
  "filename": "job_description.pdf",
  "analysis": {
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
  }
}
```

**Error Response shape** (used for all error cases below)

```json
{
  "success": false,
  "error": "Human-readable error message",
  "detail": "Optional additional detail"
}
```

| Scenario | HTTP Status |
|---|---|
| Unsupported file type / oversized file | `400 Bad Request` |
| Empty file / no extractable text | `400 Bad Request` |
| PDF/DOCX extraction failure (corrupt file) | `422 Unprocessable Entity` |
| Gemini API failure / bad response | `502 Bad Gateway` |
| Unexpected server error | `500 Internal Server Error` |

---

## 6. Folder / File Explanation

| Path | Responsibility |
|---|---|
| `app/main.py` | Creates the FastAPI app, wires up CORS, includes routers, defines global exception handlers and health endpoints. |
| `app/config.py` | Loads `.env` variables into a single `settings` object used across the app. |
| `app/routers/upload.py` | Defines `POST /analyze`: orchestrates validation → extraction → Gemini call → response. |
| `app/services/pdf_reader.py` | Extracts text from PDF files using PyMuPDF. |
| `app/services/docx_reader.py` | Extracts text from DOCX files (paragraphs + tables) using python-docx. |
| `app/services/prompt.py` | Builds the exact prompt sent to Gemini, including strict JSON-only output instructions. |
| `app/services/gemini_service.py` | Calls Gemini 2.5 Flash via the `google-genai` SDK with structured JSON output, and validates/parses the response. |
| `app/models/response_model.py` | Pydantic models: `JobDescriptionAnalysis`, `AnalyzeResponse`, `ErrorResponse`. |
| `app/utils/helpers.py` | Custom exceptions (`InvalidFileError`, `EmptyFileError`, `ExtractionError`, `GeminiServiceError`) and file validation/save/cleanup helpers. |
| `uploads/` | Temporary on-disk storage for uploaded files during processing; files are deleted immediately after each request. |

---

## 7. Notes on CORS

The frontend origin `http://localhost:5173` (Vite default) is allowed
by default. To allow additional origins (e.g. a deployed frontend),
set `ALLOWED_ORIGINS` in `.env` as a comma-separated list:

```
ALLOWED_ORIGINS=http://localhost:5173,https://your-frontend.com
```

---

## 8. Troubleshooting

- **`RuntimeError: GOOGLE_API_KEY is not set`** — Make sure you copied
  `.env.example` to `.env` and filled in a valid key, and that you're
  running `uvicorn` from inside the `backend/` directory.
- **`422` on upload** — The file is likely corrupted or password
  protected; try re-exporting the PDF/DOCX.
- **`502` from Gemini** — Check your API key/quota, and confirm network
  access to `generativelanguage.googleapis.com`.
