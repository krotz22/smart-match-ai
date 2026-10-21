import json
import re

import requests

from llm_client import call_llm, LLM_API_KEY


def format_resume_for_llm(resume):
    """Format resume data for LLM processing."""
    lines = []

    # Name
    lines.append(f"Name: {resume.get('Full Name', 'N/A')}")

    # Contact information
    contact_info = resume.get("Contact Information", {})

    if isinstance(contact_info, dict):
        lines.append(
            f"Email: {contact_info.get('email', 'N/A')}"
        )
        lines.append(
            f"Phone: {contact_info.get('phone', 'N/A')}"
        )
    else:
        lines.append(f"Contact: {contact_info}")

    # Skills
    skills = resume.get("Skills", [])

    if skills:
        lines.append("Skills:")
        lines.extend(
            [f"- {skill}" for skill in skills[:10]]
        )

    # Education
    education = resume.get("Education", [])

    if education:
        lines.append("Education:")

        for edu in education[:3]:
            if isinstance(edu, dict):
                degree = edu.get("Degree", "N/A")
                fields = edu.get("Fields of Study", "N/A")
                years = edu.get("Years Attended", "N/A")

                lines.append(
                    f"- {degree} in {fields} ({years})"
                )
            else:
                lines.append(f"- {edu}")

    # Work Experience
    work_exp = resume.get("Work Experience", [])

    if work_exp:
        lines.append("Work Experience:")

        for exp in work_exp[:5]:
            if isinstance(exp, dict):
                position = exp.get("Position", "N/A")
                company = exp.get("Company Name", "N/A")
                years = exp.get("Years Worked", "N/A")
                achievements = exp.get("Achievements", "N/A")

                lines.append(
                    f"- {position} at {company} "
                    f"({years}): {achievements}"
                )
            else:
                lines.append(f"- {exp}")

    # Certifications
    certs = resume.get("Certifications", [])

    if certs:
        lines.append("Certifications:")
        lines.extend(
            [f"- {cert}" for cert in certs[:5]]
        )

    return "\n".join(lines)


def format_jd_for_llm(jd):
    """Format job description data for LLM processing."""
    lines = []

    # Job title
    lines.append(
        f"Job Title: {jd.get('Job Title', 'N/A')}"
    )

    # Required skills
    required_skills = jd.get("Required Skills", [])

    if required_skills:
        lines.append(
            "Required Skills: "
            + ", ".join(required_skills)
        )

    # Experience
    lines.append(
        "Experience Required: "
        + str(jd.get("Experience Required", "N/A"))
    )

    # Qualifications
    qualifications = jd.get("Qualifications", [])

    if qualifications:
        lines.append(
            "Qualifications: "
            + ", ".join(qualifications)
        )

    # Responsibilities
    responsibilities = jd.get("Job Responsibilities", [])

    if responsibilities:
        lines.append(
            "Responsibilities: "
            + ", ".join(responsibilities)
        )

    return "\n".join(lines)


def extract_json_from_response(text):
    """
    Extract JSON from the LLM response.

    JSON mode should already return valid JSON, but this
    function is kept as a fallback for fenced or wrapped output.
    """

    text = text.strip()

    # First attempt: parse directly
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Second attempt: remove Markdown code fences
    cleaned_text = re.sub(
        r"```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    cleaned_text = re.sub(
        r"```\s*$",
        "",
        cleaned_text
    ).strip()

    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        pass

    # Third attempt: locate JSON object
    start = cleaned_text.find("{")
    end = cleaned_text.rfind("}")

    if start != -1 and end != -1 and end > start:
        json_str = cleaned_text[start:end + 1]

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Could not extract valid JSON from response: {e}"
            )

    raise ValueError(
        "No valid JSON object found in LLM response."
    )


def _failed_result(summary):
    """Build the standard 'could not match' result."""
    return {
        "match_score": 0,
        "matched_skills": [],
        "missing_skills": [],
        "summary": summary,
        "shortlist": False
    }


def smart_match(jd_text, resume_text, threshold=60):
    """
    Match candidate with job description using Mistral.

    Existing return structure is preserved:
        match_score
        matched_skills
        missing_skills
        summary
        shortlist
    """

    # Check API key
    if not LLM_API_KEY:
        print("❌ LLM_API_KEY not found in environment.")
        return _failed_result("API Key not configured.")
    prompt = f"""
    You are a strict, evidence-based AI recruitment assistant.
    
    Evaluate the candidate ONLY against the job description.
    The candidate may be shortlisted only if the required skills
    are genuinely supported by the resume.
    
    JOB REQUIREMENTS:
    - Data Science and Machine Learning modelling: required
    - Python programming: required
    - Complex SQL queries: required
    - Cloud platforms (AWS, Azure, GCP): preferred, not mandatory
    - Teamwork, learning ability, analytical thinking,
      problem-solving and communication: desired
    
    STRICT EVALUATION RULES:
    
    1. Score from 0 to 100 based on demonstrated job relevance.
    2. Python: 30 points.
    3. Data Science and Machine Learning: 30 points.
    4. SQL, including complex queries: 25 points.
    5. Cloud knowledge: 5 points.
    6. Personal skills and relevant project evidence: 10 points.
    
    7. Award points only for skills supported by the resume.
    8. Do not assume a skill from the candidate's degree,
       unrelated projects, or general engineering knowledge.
    9. Basic electronics knowledge does NOT establish Python,
       machine learning, data science, or complex SQL skills.
    10. Put every unsupported required skill in missing_skills.
    11. Cloud is preferred, so its absence alone must not disqualify
        an otherwise qualified candidate.
    12. A candidate missing any of the three core requirements
        (Python, Data Science/Machine Learning, or complex SQL)
        must not be shortlisted.
    13. Do not invent experience, skills, projects, or qualifications.
    14. Explain the evaluation briefly and factually.
    
    Return ONLY a valid JSON object with exactly these keys:
    {{
      "match_score": 0,
      "matched_skills": [],
      "missing_skills": [],
      "summary": "Evidence-based explanation",
      "shortlist": false
    }}
    
    Job Description:
    {jd_text}
    
    Candidate Resume:
    {resume_text}
    """
    # Prompt (the JSON shape is spelled out because Mistral
    # does not use a response schema like Gemini did)
    try:
        print("🔄 Sending request to Mistral...")

        message_content = call_llm(
            prompt,
            temperature=0.3,
            max_tokens=2048
        )

        print("✅ Mistral response received.")

        # Extract JSON
        result = extract_json_from_response(message_content)

        # Validate result
        match_score = int(result.get("match_score", 0))

        # Keep score safely between 0 and 100
        match_score = max(0, min(100, match_score))

        matched_skills = result.get("matched_skills", [])
        missing_skills = result.get("missing_skills", [])
        summary = result.get("summary", "Could not generate summary.")

        # Shortlist is controlled by our threshold
        shortlist = match_score >= threshold

        final_result = {
            "match_score": match_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "summary": summary,
            "shortlist": shortlist
        }

        print(f"✅ Match score: {match_score}%")
        print(f"✅ Shortlisted: {shortlist}")

        return final_result

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        print(f"❌ LLM HTTP error: {e}")

        return _failed_result(
            f"LLM API error {status}. "
            "Check the API key, model name and quota."
        )

    except requests.exceptions.Timeout as e:
        print(f"❌ LLM request timed out: {e}")
        return _failed_result("LLM API request timed out. Please try again.")

    except requests.exceptions.RequestException as e:
        print(f"❌ LLM request error: {e}")
        return _failed_result("Could not connect to the LLM API.")

    except json.JSONDecodeError as e:
        print(f"❌ JSON decoding error: {e}")
        return _failed_result("LLM returned invalid JSON.")

    except (KeyError, ValueError, TypeError) as e:
        print(f"❌ Response parsing error: {e}")
        return _failed_result(f"Could not parse LLM result: {e}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return _failed_result("An unexpected error occurred.")
