import io
import fitz  # PyMuPDF
import json
import os
import requests
import re
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Headers for Gemini API - Key is passed as query param in the final URL
HEADERS = {
    "Content-Type": "application/json"
}

# Gemini endpoint (using gemini-2.5-pro for complex structured tasks)
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-pro:generateContent"


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
        # If JSON parsing fails, try to find the largest JSON-like structure
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        raise ValueError(f"Could not extract valid JSON from response: {e}")


def create_default_response(text=""):
    """Create default response structure when parsing fails"""
    return {
        "Full Name": "N/A",
        "Contact Information": {"email": "N/A", "phone": "N/A"},
        "Skills": [],
        "Education": [],
        "Work Experience": [],
        "Certifications": [],
        "Raw Text": text
    }


def parse_resume_with_llm_binary(file_bytes: bytes):
    """Parse PDF resume from binary data using Gemini LLM"""
    text = ""
    
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not found in environment.")
        return create_default_response()

    try:
        # 1. Extract Text from PDF (PyMuPDF)
        stream = io.BytesIO(file_bytes)
        doc = fitz.open(stream=stream, filetype="pdf")
        
        for page in doc:
            text += page.get_text()
        doc.close()
        
        if not text.strip():
            raise ValueError("No text could be extracted from the PDF")

        # 2. Prepare Prompt for Gemini
        prompt = f"""
You are an expert resume parser AI. Extract information from the following resume text and respond with ONLY a valid JSON object.
ENSURE YOUR RESPONSE STARTS AND ENDS WITH THE JSON BRACES {{...}}.

Required JSON format:
{{
    "Full Name": "string",
    "Contact Information": {{
        "email": "string",
        "phone": "string"
    }},
    "Skills": ["skill1", "skill2", "skill3"],
    "Education": [{{
        "Degree": "string",
        "Fields of Study": "string",
        "Years Attended": "string"
    }}],
    "Work Experience": [{{
        "Position": "string",
        "Company Name": "string",
        "Years Worked": "string",
        "Achievements": "string"
    }}],
    "Certifications": ["cert1", "cert2"]
}}

Resume Text (limited to 4000 characters for safety):
{text[:4000]}
        """

        # 3. Call Gemini API
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "config": {
                "temperature": 0.3,
                "maxOutputTokens": 2000
            }
        }

        # API Key appended to URL for this endpoint structure
        url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        
        response = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()

        response_data = response.json()
        message_content = response_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()

        # 4. Extract and Validate JSON
        structured = extract_json_from_response(message_content)
        structured["Raw Text"] = text

        return structured

    except requests.exceptions.RequestException as e:
        print(f"❌ API request error: {e}")
        return create_default_response(text)
    except fitz.fitz.FileDataError as e:
        print(f"❌ PDF parsing error: {e}")
        return create_default_response()
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return create_default_response(text)