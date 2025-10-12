import io
import fitz  # PyMuPDF
import json
import os
import requests
import re
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-pro:generateContent"

# Validate API key
if not GEMINI_API_KEY:
    print("⚠️  WARNING: GEMINI_API_KEY not found in environment variables")

HEADERS = {
    "Content-Type": "application/json"
}

def extract_json_from_response(text):
    """Extract the first valid JSON object from text response"""
    try:
        # Try to find JSON block using regex (non-greedy match)
        json_match = re.search(r'\{.*?\}', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            # Try to parse the extracted JSON
            return json.loads(json_str)
        else:
            # If no JSON block found, try parsing the entire text
            return json.loads(text)
    except json.JSONDecodeError:
        # If JSON parsing fails, try to find the largest JSON-like structure
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        raise ValueError("Could not extract valid JSON from response")

def parse_resume_with_llm_binary(file_bytes: bytes):
    """Parse PDF resume from binary data using Gemini LLM"""
    try:
        # Create BytesIO stream from bytes
        stream = io.BytesIO(file_bytes)
        
        # Open PDF with PyMuPDF
        doc = fitz.open(stream=stream, filetype="pdf")
        
        # Extract text from all pages
        text = ""
        for page in doc:
            text += page.get_text()
        
        doc.close()  # Close the document
        
        if not text.strip():
            raise ValueError("No text could be extracted from the PDF")

        prompt = f"""
You are an expert resume parser AI. Extract information from the following resume text and respond with ONLY a valid JSON object.

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

Resume Text:
{text[:4000]}
        """

        data = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "config": {
                "temperature": 0.3,
                "maxOutputTokens": 2000
            }
        }

        # API Key appended to URL for Gemini endpoint structure
        url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        response = requests.post(url, headers=HEADERS, json=data, timeout=30)
        response.raise_for_status()

        response_data = response.json()
        message_content = response_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()

        # Extract JSON from response
        structured = extract_json_from_response(message_content)
        
        # Add raw text to the result
        structured["Raw Text"] = text

        return structured

    except requests.exceptions.RequestException as e:
        print(f"❌ API request error in parse_resume_with_llm_binary: {e}")
        print(f"❌ GEMINI_API_KEY configured: {'Yes' if GEMINI_API_KEY else 'No'}")
        return create_default_response(text if 'text' in locals() else "")
    except fitz.fitz.FileDataError as e:
        print(f"❌ PDF parsing error in parse_resume_with_llm_binary: {e}")
        return create_default_response("")
    except ValueError as e:
        print(f"❌ JSON parsing error in parse_resume_with_llm_binary: {e}")
        return create_default_response(text if 'text' in locals() else "")
    except Exception as e:
        print(f"❌ Unexpected error in parse_resume_with_llm_binary: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        return create_default_response(text if 'text' in locals() else "")

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
