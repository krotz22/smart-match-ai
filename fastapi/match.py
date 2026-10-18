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

    # Prompt (the JSON shape is spelled out because Mistral
    # does not use a response schema like Gemini did)
    prompt = f"""
You are an AI recruitment assistant.

Evaluate the candidate's resume against the job description.

Follow these rules carefully:

1. match_score must be an integer from 0 to 100.
2. matched_skills must contain skills clearly supported by the resume.
3. missing_skills must contain important required skills that are not clearly supported by the resume.
4. summary must be a brief and factual evaluation.
5. shortlist must be true when the match_score is greater than or equal to {threshold}.
6. Do not invent experience that is not present in the resume.
7. Consider skills, education, experience, projects, and responsibilities.
8. Return ONLY a JSON object with exactly these keys:
{{"match_score": 0, "matched_skills": ["skill"], "missing_skills": ["skill"], "summary": "text", "shortlist": true}}

Job Description:
{jd_text}

Candidate Resume:
{resume_text}
"""

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
