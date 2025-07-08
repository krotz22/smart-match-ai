import ollama
import json

def format_resume_for_llm(resume):
    lines = []
    lines.append(f"Name: {resume.get('Full Name', 'N/A')}")
    lines.append(f"Email: {resume.get('Contact Information', {}).get('email', 'N/A')}")
    lines.append(f"Phone: {resume.get('Contact Information', {}).get('phone', 'N/A')}")
    lines.append("Skills:")
    lines.extend(resume.get("Skills", []))

    for edu in resume.get("Education", []):
        degree = edu.get("Degree", "N/A")
        fields = edu.get("Fields of Study")
        fields_str = ", ".join(fields) if isinstance(fields, list) else (fields or "N/A")
        years = edu.get("Years Attended", "N/A")
        lines.append(f"Education: {degree} in {fields_str} ({years})")

    lines.append("Work Experience:")
    for exp in resume.get("Work Experience", []):
        lines.append(str(f"{exp.get('Position', 'N/A')} at {exp.get('Company Name', 'N/A')} ({exp.get('Years Worked', 'N/A')}): {exp.get('Achievements', 'N/A')}") or "N/A")

    lines.append("Certifications:")
    lines.extend(resume.get("Certifications", []))

    return "\n".join([str(line) if line is not None else "N/A" for line in lines])

def format_jd_for_llm(jd):
    return f"""
Job Title: {jd.get("Job Title", "N/A")}
Required Skills: {', '.join(jd.get("Required Skills", []))}
Experience Required: {jd.get("Experience Required", "N/A")}
Qualifications: {', '.join(jd.get("Qualifications", []))}
Responsibilities: {', '.join(jd.get("Job Responsibilities", []))}
"""

def smart_match(jd_text, resume_text, threshold=60):
    prompt = f"""
You are an AI recruitment assistant. Evaluate the following candidate against the job description.
Give a match score (0-100), list matched and missing skills, and explain your reasoning.
Respond ONLY in JSON format with keys: match_score, matched_skills, missing_skills, summary, shortlist.

Job Description:
{jd_text}

Candidate Resume:
{resume_text}
"""

    try:
        response = ollama.chat(
            model="mistral",
            messages=[{"role": "user", "content": prompt}]
        )
        result = json.loads(response['message']['content'])
        result["match_score"] = int(result.get("match_score", 0))
        result["shortlist"] = result["match_score"] >= threshold

        return result
    except Exception as e:
        print("❌ LLM parse error:", e)
        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "summary": "Could not parse result.",
            "shortlist": False
        }
