import json
import os
import requests
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Headers for Mistral API
headers = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json"
}

# Mistral endpoint
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

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
        lines.extend([f"- {skill}" for skill in skills[:10]])  # Limit to 10 skills
    
    # Education
    education = resume.get("Education", [])
    if education:
        lines.append("Education:")
        for edu in education[:3]:  # Limit to 3 entries
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
        for exp in work_exp[:5]:  # Limit to 5 entries
            if isinstance(exp, dict):
                position = exp.get('Position', 'N/A')
                company = exp.get('Company Name', 'N/A')
                years = exp.get('Years Worked', 'N/A')
                achievements = exp.get('Achievements', 'N/A')
                lines.append(f"- {position} at {company} ({years}): {achievements}")
            else:
                lines.append(f"- {exp}")
    
    # Certifications
    certs = resume.get("Certifications", [])
    if certs:
        lines.append("Certifications:")
        lines.extend([f"- {cert}" for cert in certs[:5]])  # Limit to 5 certs
    
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

def smart_match(jd_text, resume_text, threshold=60):
    """Match candidate with job description using Mistral LLM"""
    prompt = f"""
You are an AI recruitment assistant. Evaluate the candidate's resume against the job description.

Provide ONLY a valid JSON response with these exact keys:
{{
    "match_score": 75,
    "matched_skills": ["skill1", "skill2"],
    "missing_skills": ["skill3", "skill4"],
    "summary": "Brief evaluation summary",
    "shortlist": true
}}

Job Description:
{jd_text}

Candidate Resume:
{resume_text}
"""

    payload = {
        "model": "mistral-large-latest",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 1000
    }

    try:
        response = requests.post(MISTRAL_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        message = response.json()["choices"][0]["message"]["content"].strip()
        
        # Extract JSON from response
        import re
        json_match = re.search(r'\{.*?\}', message, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
        else:
            result = json.loads(message)

        # Ensure required fields and types
        result["match_score"] = int(result.get("match_score", 0))
        result["matched_skills"] = result.get("matched_skills", [])
        result["missing_skills"] = result.get("missing_skills", [])
        result["summary"] = result.get("summary", "Could not generate summary.")
        result["shortlist"] = result["match_score"] >= threshold

        return result
        
    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError) as e:
        print(f"❌ API call or JSON parsing error: {e}")
        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "summary": "Could not parse result due to an error.",
            "shortlist": False
        }
