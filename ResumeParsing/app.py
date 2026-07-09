import json
from pathlib import Path

import streamlit as st

from src.pipeline import parse_resume_pipeline
from src.utils import save_uploaded_file


st.set_page_config(
    page_title="RADIX Resume Parser",
    page_icon="📄",
    layout="centered",
)

st.title("📄 RADIX Resume Parser")
st.caption("Role 2 · Resume Parsing for Talent Match Hackathon")

st.markdown(
    """
Upload a **PDF** or **DOCX** resume.  
This tool extracts resume text, sends it to Gemini, and generates structured JSON.
"""
)

uploaded_file = st.file_uploader("Upload resume", type=["pdf", "docx"])

if uploaded_file:
    saved_path = save_uploaded_file(uploaded_file, Path("input/resumes"))
    st.success(f"Uploaded: `{saved_path.name}`")

    if st.button("Parse Resume", type="primary"):
        with st.spinner("Extracting and parsing resume..."):
            try:
                result = parse_resume_pipeline(str(saved_path))

                st.success("Resume parsed successfully ✅")

                st.subheader("Structured JSON Output")
                st.json(result["parsed_json"])

                st.download_button(
                    label="Download JSON",
                    data=json.dumps(result["parsed_json"], indent=2),
                    file_name=f"{Path(saved_path).stem}_parsed.json",
                    mime="application/json",
                )

                with st.expander("View extracted raw text"):
                    st.text(result["raw_text"])

                st.info(f"Saved JSON: `{result['json_output_path']}`")

            except Exception as exc:
                st.error("Parsing failed.")
                st.exception(exc)

else:
    st.info("Upload a resume to begin.")
