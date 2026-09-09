import json
import os
import re
import requests
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Headers for Gemini API
# API key is sent securely through the request header.
HEADERS = {
    "Content-Type": "application/json",
    "x-goog-api-key": GEMINI_API_KEY or ""
}

# Gemini endpoint
# Gemini 2.5 Pro supports structured JSON output.
GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/gemini-2.5-pro:generateContent"
)


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
                position = exp.get(
                    "Position",
                    "N/A"
                )

                company = exp.get(
                    "Company Name",
                    "N/A"
                )

                years = exp.get(
                    "Years Worked",
                    "N/A"
                )

                achievements = exp.get(
                    "Achievements",
                    "N/A"
                )

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
    required_skills = jd.get(
        "Required Skills",
        []
    )

    if required_skills:
        lines.append(
            "Required Skills: "
            + ", ".join(required_skills)
        )

    # Experience
    lines.append(
        "Experience Required: "
        + str(
            jd.get(
                "Experience Required",
                "N/A"
            )
        )
    )

    # Qualifications
    qualifications = jd.get(
        "Qualifications",
        []
    )

    if qualifications:
        lines.append(
            "Qualifications: "
            + ", ".join(qualifications)
        )

    # Responsibilities
    responsibilities = jd.get(
        "Job Responsibilities",
        []
    )

    if responsibilities:
        lines.append(
            "Responsibilities: "
            + ", ".join(responsibilities)
        )

    return "\n".join(lines)


def extract_json_from_response(text):
    """
    Extract JSON from Gemini response.

    Structured output should already return valid JSON,
    but this function is kept as a fallback so existing
    behavior remains compatible.
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
        "No valid JSON object found in Gemini response."
    )


def smart_match(jd_text, resume_text, threshold=60):
    """
    Match candidate with job description using Gemini LLM.

    Existing return structure is preserved:
        match_score
        matched_skills
        missing_skills
        summary
        shortlist
    """

    # Check API key
    if not GEMINI_API_KEY:
        print(
            "❌ GEMINI_API_KEY not found in environment."
        )

        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "summary": "API Key not configured.",
            "shortlist": False
        }

    # Prompt
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
8. Return ONLY the requested JSON structure.

Job Description:
{jd_text}

Candidate Resume:
{resume_text}
"""

    # Gemini request
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1000,

            # Force JSON output
            "responseMimeType": "application/json",

            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "match_score": {
                        "type": "INTEGER",
                        "minimum": 0,
                        "maximum": 100
                    },

                    "matched_skills": {
                        "type": "ARRAY",
                        "items": {
                            "type": "STRING"
                        }
                    },

                    "missing_skills": {
                        "type": "ARRAY",
                        "items": {
                            "type": "STRING"
                        }
                    },

                    "summary": {
                        "type": "STRING"
                    },

                    "shortlist": {
                        "type": "BOOLEAN"
                    }
                },

                "required": [
                    "match_score",
                    "matched_skills",
                    "missing_skills",
                    "summary",
                    "shortlist"
                ]
            }
        }
    }

    try:
        print("🔄 Sending request to Gemini...")

        response = requests.post(
            GEMINI_API_URL,
            headers=HEADERS,
            json=payload,
            timeout=60
        )

        # Helpful debugging information
        if not response.ok:
            print(
                f"❌ Gemini API Error: "
                f"{response.status_code}"
            )

            print(
                "Gemini response:"
            )

            print(
                response.text
            )

            response.raise_for_status()

        # Parse response
        response_data = response.json()

        # Ensure candidates exists
        candidates = response_data.get(
            "candidates"
        )

        if not candidates:
            raise ValueError(
                "Gemini returned no candidates."
            )

        # Extract generated content
        candidate = candidates[0]

        content = candidate.get(
            "content",
            {}
        )

        parts = content.get(
            "parts",
            []
        )

        if not parts:
            raise ValueError(
                "Gemini returned no content parts."
            )

        message_content = parts[0].get(
            "text",
            ""
        ).strip()

        if not message_content:
            raise ValueError(
                "Gemini returned an empty response."
            )

        print("✅ Gemini response received.")

        # Extract JSON
        result = extract_json_from_response(
            message_content
        )

        # Validate result
        match_score = int(
            result.get(
                "match_score",
                0
            )
        )

        # Keep score safely between 0 and 100
        match_score = max(
            0,
            min(100, match_score)
        )

        matched_skills = result.get(
            "matched_skills",
            []
        )

        missing_skills = result.get(
            "missing_skills",
            []
        )

        summary = result.get(
            "summary",
            "Could not generate summary."
        )

        # Shortlist is controlled by our threshold
        shortlist = match_score >= threshold

        final_result = {
            "match_score": match_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "summary": summary,
            "shortlist": shortlist
        }

        print(
            f"✅ Match score: {match_score}%"
        )

        print(
            f"✅ Shortlisted: {shortlist}"
        )

        return final_result

    except requests.exceptions.HTTPError as e:
        print(
            f"❌ Gemini HTTP error: {e}"
        )

        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "summary": (
                "Gemini API request failed. "
                "Please check the API configuration."
            ),
            "shortlist": False
        }

    except requests.exceptions.Timeout as e:
        print(
            f"❌ Gemini request timed out: {e}"
        )

        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "summary": (
                "Gemini API request timed out. "
                "Please try again."
            ),
            "shortlist": False
        }

    except requests.exceptions.RequestException as e:
        print(
            f"❌ Gemini request error: {e}"
        )

        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "summary": (
                "Could not connect to Gemini API."
            ),
            "shortlist": False
        }

    except json.JSONDecodeError as e:
        print(
            f"❌ JSON decoding error: {e}"
        )

        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "summary": (
                "Gemini returned invalid JSON."
            ),
            "shortlist": False
        }

    except (KeyError, ValueError, TypeError) as e:
        print(
            f"❌ Response parsing error: {e}"
        )

        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "summary": (
                f"Could not parse Gemini result: {e}"
            ),
            "shortlist": False
        }

    except Exception as e:
        print(
            f"❌ Unexpected error: {e}"
        )

        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "summary": (
                "An unexpected error occurred."
            ),
            "shortlist": False
        }
