import json
import requests
import pypdf

# Config
BASE_URL = "http://localhost:8000"
RESUME_PATH = "C:/Users/Admin/Downloads/Priya Menon.pdf"
JD_PATH = "C:/Users/Admin/Downloads/Microsoft - Software Engineer.pdf"

def extract_pdf_text(filepath):
    reader = pypdf.PdfReader(filepath)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()

def run_tests():
    print("=== STARTING END-TO-END ENDPOINT TESTS ===")
    
    # 1. Health check
    print("\n1. Testing health check...")
    res = requests.get(f"{BASE_URL}/health")
    print("Health Status Code:", res.status_code)
    print("Response:", res.json())
    
    # 2. Parse Resume
    print("\n2. Extracting and parsing resume (Priya Menon.pdf)...")
    resume_text = extract_pdf_text(RESUME_PATH)
    payload_resume = {
        "filename": "Priya Menon.pdf",
        "text": resume_text[:6000]  # Limit tokens for testing
    }
    res = requests.post(f"{BASE_URL}/api/parse-resume", json=payload_resume)
    print("Parse Resume Status Code:", res.status_code)
    if res.status_code == 200:
        candidate_profile = res.json()
        print("Candidate Name:", candidate_profile.get("name"))
        print("Candidate Email:", candidate_profile.get("email"))
        print("Skills Extracted Count:", len(candidate_profile.get("skills", [])))
        print("Education:", candidate_profile.get("education"))
    else:
        print("Error:", res.text)
        return

    # 3. Analyze JD
    print("\n3. Extracting and analyzing JD (Microsoft - Software Engineer.pdf)...")
    jd_text = extract_pdf_text(JD_PATH)
    payload_jd = {
        "filename": "Microsoft - Software Engineer.pdf",
        "text": jd_text[:6000]
    }
    res = requests.post(f"{BASE_URL}/api/analyze-jd", json=payload_jd)
    print("Analyze JD Status Code:", res.status_code)
    if res.status_code == 200:
        analyzed_jd = res.json()
        print("Job Seniority:", analyzed_jd.get("seniority"))
        print("Required Skills Count:", len(analyzed_jd.get("skills", [])))
        print("Technologies Count:", len(analyzed_jd.get("technologies", [])))
    else:
        print("Error:", res.text)
        return

    # 4. Talent Check
    print("\n4. Running Talent Check on Candidate against Google standards...")
    payload_check = {
        "profile": candidate_profile,
        "company": "Google"
    }
    res = requests.post(f"{BASE_URL}/api/check", json=payload_check)
    print("Talent Check Status Code:", res.status_code)
    if res.status_code == 200:
        talent_check = res.json()
        print("Google Readiness Score:", talent_check.get("readiness_score"))
        print("Overall Status:", talent_check.get("overall_readiness"))
        print("Recommendations Count:", len(talent_check.get("recommendations", [])))
    else:
        print("Error:", res.text)
        return

    # 5. Skill Match
    print("\n5. Running Skill Match between Candidate and Microsoft JD...")
    payload_match = {
        "profile": candidate_profile,
        "jd": analyzed_jd
    }
    res = requests.post(f"{BASE_URL}/api/skill-match", json=payload_match)
    print("Skill Match Status Code:", res.status_code)
    if res.status_code == 200:
        match_result = res.json()
        print("ATS Match Score:", match_result.get("match_score"))
        print("Eligibility Label:", match_result.get("eligibility"))
        print("Direct Matched Skills:", match_result.get("matched_skills"))
        print("Fuzzy Matches:", [f"{pm['candidate_skill']} ~ {pm['jd_skill']} ({pm['similarity']}%)" for pm in match_result.get("partial_matches", [])])
        print("Missing Required Skills:", match_result.get("missing_skills"))
        print("Career Recommendations Count:", len(match_result.get("recommendations", [])))
    else:
        print("Error:", res.text)
        return

    print("\n=== ALL TESTS PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_tests()
