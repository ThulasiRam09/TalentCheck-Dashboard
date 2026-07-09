# 🎯 TalentCheck Dashboard

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/JavaScript-Frontend-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JavaScript">
  <img src="https://img.shields.io/badge/Status-Hackathon%20MVP-orange?style=for-the-badge" alt="Status">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

TalentCheck Dashboard is an all-in-one HR-tech solution designed to optimize the recruitment workflow. By leveraging automation and intelligent analysis, this platform helps recruiters and candidates connect faster and more effectively — giving candidates data-driven clarity on how ready they really are for a specific role, instead of guessing and hoping.

---

## ✨ Core Features

| Feature | Description |
| :--- | :--- |
| 📄 **JD Analysis** | Automatically parses Job Descriptions (PDF/DOCX) and extracts required skills, mapped to the 12 RADIX skill categories. |
| 📑 **Resume Parsing** | Converts unstructured PDF/Word resumes into structured, comparable data — no manual re-entry needed. |
| 👤 **Profile Builder** | Auto-populates a candidate profile straight from the parsed resume; candidates just fill in the extras (education, certifications, preferred roles). |
| ✅ **Talent Check** | A comprehensive scoring system that compares a candidate's profile against a company + role's expected bar across all 12 skillsets, with a readiness score, tier, and top focus areas. |
| 🔍 **Skill Matching** | Compares a candidate's skills against one specific job posting, returning a match score plus matched and missing skills. |

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | HTML5 + vanilla JavaScript (fetch API) — lightweight, dependency-free, single-page dashboard |
| **Backend** | Python 3 + [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn |
| **Data storage** | JSON (session-based in-memory store for the hackathon build; swappable for Supabase/Postgres) |
| **Resume/JD parsing** | [pdfplumber](https://github.com/jsvine/pdfplumber) (PDF), [python-docx](https://python-docx.readthedocs.io/) (Word) |
| **Skill extraction** | Section-aware keyword mapping across the 12 RADIX categories (deterministic — no external API calls, no latency risk during a live demo) |
| **Fuzzy skill matching** | [RapidFuzz](https://github.com/maxbachmann/RapidFuzz) for alias + similarity-based skill comparison |
| **Validation** | [Pydantic](https://docs.pydantic.dev/) |

> **Why no LLM API in the MVP?** Keyword + section-based extraction is fast, free, and has zero risk of a live network/API failure during a demo — every skill hit also comes with its evidence phrase, so it's fully explainable. The extraction layer is isolated behind one function, so swapping in an LLM (OpenAI, Claude, etc.) later is a drop-in change with no impact on the rest of the app.

---

## 🚀 Getting Started

### Prerequisites
* [Python 3.10+](https://www.python.org/)
* [Git](https://git-scm.com/)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Indra0099/TalentCheck-Dashboard.git
   cd TalentCheck-Dashboard
   ```

2. Install backend dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Run the backend server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

4. Open the frontend:
   Open `frontend/index.html` directly in your browser (or serve it with any static file server). It talks to `http://localhost:8000` by default.

### Quick Usage

1. **Upload a JD** → skills are extracted and categorized automatically
2. **Upload a resume** → your profile is built for you, no manual skill entry
3. **Fill in the extras** in Profile Builder (education, certifications, preferred roles)
4. **Pick a company + role** in Talent Check and hit **Test** → see your readiness score
5. **Run Skill Matching** → see exactly how you match the JD you uploaded in step 1

---

## 📂 Project Structure

```
TalentCheck-Dashboard/
├── backend/
│   ├── main.py                     # FastAPI app — all 5 phases wired together
│   ├── requirements.txt
│   ├── data/
│   │   └── company_skillsets.json  # Company + role skill-level requirements
│   └── services/
│       ├── extraction.py           # JD + resume skill extraction
│       ├── talent_check.py         # Readiness scoring logic
│       └── skill_match.py          # JD-specific fuzzy matching
├── frontend/
│   └── index.html                  # Single-page dashboard UI
└── README.md
```

---

## 👥 Project Team

This project is a collaborative effort by the following team members:

| Phase | Contributor |
| :--- | :--- |
| **JD Analysis** | S. Chethan |
| **Resume Parsing** | I. Mahesh Reddy |
| **Profile Builder** | A. Indra Varshit |
| **Talent Check** | N. Thulasi Ram |
| **Skill Matching** | J. Jaswanth |

---

## 📄 License

This project was built as part of a hackathon MVP. Add your preferred license here (e.g. MIT) before making the repo public if you plan to share it further.

------------------------------------------------------------------------

⭐ Star this repository if you find it useful! :)
