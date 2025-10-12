import json
import os
import requests
import re
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Headers for Gemini API - Key is passed as query param in the final URL
HEADERS = {
    "Content-Type": "application/json"
}

# Gemini endpoint (using gemini-2.5-pro for complex structured tasks)
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-pro:generateContent"


def format_resume_for_llm(resume):
    """Format resume data for LLM processing"""
    lines = []
    lines.append(f"Name: {resume.get('Full Name', 'N/A')}")
    
    contact_info = resume.get('Contact Information', {})
    if isinstance(contact_info, dict):
        lines.append(f"Email: {contact_info.get('email', 'N/A')}")
        lines.append(f"Phone: {contact_info.get('phone', 'N/A')}")
    else:
        lines.append(f"Contact: {contact_info}")
    
    # Skills
    skills = resume.get("Skills", [])
    if skills:
        lines.append("Skills:")
        lines.extend([f"- {skill}" for skill in skills[:10]])
    
    # Education
    education = resume.get("Education", [])
    if education:
        lines.append("Education:")
        for edu in education[:3]:
            if isinstance(edu, dict):
                degree = edu.get("Degree", "N/A")
                fields = edu.get("Fields of Study", "N/A")
                years = edu.get("Years Attended", "N/A")
                lines.append(f"- {degree} in {fields} ({years})")
            else:
                lines.append(f"- {edu}")
    
    # Work Experience
    work_exp = resume.get("Work Experience", [])
    if work_exp:
        lines.append("Work Experience:")
        for exp in work_exp[:5]:
            if isinstance(exp, dict):
                position = exp.get('Position', 'N/A')
                company = exp.get('Company Name', 'N/A')
                years = exp.get('Years Worked', 'N/A')
                # Note: Achievements may contain detailed text, so we include it.
                achievements = exp.get('Achievements', 'N/A') 
                lines.append(f"- {position} at {company} ({years}): {achievements}")
            else:
                lines.append(f"- {exp}")
    
    # Certifications
    certs = resume.get("Certifications", [])
    if certs:
        lines.append("Certifications:")
        lines.extend([f"- {cert}" for cert in certs[:5]])
    
    return "\n".join(lines)


def format_jd_for_llm(jd):
    """Format job description for LLM processing"""
    lines = []
    lines.append(f"Job Title: {jd.get('Job Title', 'N/A')}")
    
    required_skills = jd.get("Required Skills", [])
    if required_skills:
        lines.append(f"Required Skills: {', '.join(required_skills)}")
    
    lines.append(f"Experience Required: {jd.get('Experience Required', 'N/A')}")
    
    qualifications = jd.get("Qualifications", [])
    if qualifications:
        lines.append(f"Qualifications: {', '.join(qualifications)}")
    
    responsibilities = jd.get("Job Responsibilities", [])
    if responsibilities:
        lines.append(f"Responsibilities: {', '.join(responsibilities)}")
    
    return "\n".join(lines)


def extract_json_from_response(text):
    """Extract the first valid JSON object from text response"""
    try:
        # Try to find JSON block using regex (non-greedy match)
        json_match = re.search(r'\{.*?\}', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            # Simple cleanup for common LLM output issues
            json_str = json_str.replace('},\n]', '}]').replace(',\n}', '}')
            return json.loads(json_str)
        else:
            return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not extract valid JSON from response: {e}")


def smart_match(jd_text, resume_text, threshold=60):
    """Match candidate with job description using Gemini LLM"""
    
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not found in environment.")
        return {
            "match_score": 0, "matched_skills": [], "missing_skills": [],
            "summary": "API Key not configured.", "shortlist": False
        }

    prompt = f"""
You are an AI recruitment assistant. Evaluate the candidate's resume against the job description.
Your response MUST be ONLY a valid JSON object.
ENSURE YOUR RESPONSE STARTS AND ENDS WITH THE JSON BRACES {{...}}.

Provide ONLY a valid JSON response with these exact keys and data types:
{{
    "match_score": 75, // integer score from 0 to 100
    "matched_skills": ["skill1", "skill2"], // array of strings
    "missing_skills": ["skill3", "skill4"], // array of strings
    "summary": "Brief evaluation summary", // string
    "shortlist": true // boolean
}}

Job Description:
{jd_text}

Candidate Resume:
{resume_text}
"""
    # 1. Call Gemini API
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "config": {
            "temperature": 0.3,
            "maxOutputTokens": 1000
        }
    }

    # API Key appended to URL for this endpoint structure
    url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"

    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        message_content = response_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()

        # 2. Extract and Validate JSON
        result = extract_json_from_response(message_content)

        # 3. Ensure required fields and types
        result["match_score"] = int(result.get("match_score", 0))
        result["matched_skills"] = result.get("matched_skills", [])
        result["missing_skills"] = result.get("missing_skills", [])
        result["summary"] = result.get("summary", "Could not generate summary.")
        # Determine shortlist based on threshold
        result["shortlist"] = result["match_score"] >= threshold

        return result
        
<<<<<<< HEAD
    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"❌ API call or JSON parsing error: {e}")
=======
    except requests.exceptions.RequestException as e:
        print(f"❌ API request error in smart_match: {e}")
        print(f"❌ MISTRAL_API_KEY configured: {'Yes' if MISTRAL_API_KEY else 'No'}")
>>>>>>> 8b418d85c60c2ee4c48d2ff43b329bbd7a8be967
        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
<<<<<<< HEAD
            "summary": f"Could not parse result due to an error: {e}",
=======
            "summary": f"API request failed: {str(e)}",
            "shortlist": False
        }
    except (json.JSONDecodeError, KeyError) as e:
        print(f"❌ JSON parsing error in smart_match: {e}")
        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "summary": f"Could not parse API response: {str(e)}",
            "shortlist": False
        }
    except Exception as e:
        print(f"❌ Unexpected error in smart_match: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "summary": f"Unexpected error: {str(e)}",
>>>>>>> 8b418d85c60c2ee4c48d2ff43b329bbd7a8be967
            "shortlist": False
        }