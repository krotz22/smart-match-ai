import io
import fitz  # PyMuPDF
import json
import os
import requests
import re
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# GEMINI CONFIGURATION
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/gemini-3-flash-preview:generateContent"
)

# Validate API key
if not GEMINI_API_KEY:
    print(
        "⚠️ WARNING: GEMINI_API_KEY not found "
        "in environment variables"
    )

# Send API key through header instead of URL
HEADERS = {
    "Content-Type": "application/json",
    "x-goog-api-key": GEMINI_API_KEY or ""
}


# ============================================================
# JSON EXTRACTION
# ============================================================

def extract_json_from_response(text):
    """Extract the first valid JSON object from Gemini response."""

    text = text.strip()

    # --------------------------------------------------------
    # 1. Try direct JSON parsing
    # --------------------------------------------------------
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # --------------------------------------------------------
    # 2. Remove Markdown code fences
    # --------------------------------------------------------
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

    # --------------------------------------------------------
    # 3. Find JSON object inside response
    # --------------------------------------------------------
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
        "Could not extract valid JSON from Gemini response"
    )


# ============================================================
# RESUME PARSER
# ============================================================

def parse_resume_with_llm_binary(file_bytes: bytes):
    """
    Parse PDF resume from binary data using Gemini LLM.
    """

    text = ""

    try:
        # ----------------------------------------------------
        # Create BytesIO stream from uploaded PDF bytes
        # ----------------------------------------------------
        stream = io.BytesIO(file_bytes)

        # ----------------------------------------------------
        # Open PDF using PyMuPDF
        # ----------------------------------------------------
        doc = fitz.open(
            stream=stream,
            filetype="pdf"
        )

        # ----------------------------------------------------
        # Extract text from all pages
        # ----------------------------------------------------
        for page in doc:
            text += page.get_text()

        # Close document
        doc.close()

        # ----------------------------------------------------
        # Validate extracted text
        # ----------------------------------------------------
        if not text.strip():
            raise ValueError(
                "No text could be extracted from the PDF"
            )

        # ----------------------------------------------------
        # Gemini prompt
        # ----------------------------------------------------
        prompt = f"""
You are an expert resume parser AI.

Extract structured information from the resume text below.

Return ONLY a valid JSON object.

Use exactly this structure:

{{
    "Full Name": "string",
    "Contact Information": {{
        "email": "string",
        "phone": "string"
    }},
    "Skills": [
        "skill1",
        "skill2",
        "skill3"
    ],
    "Education": [
        {{
            "Degree": "string",
            "Fields of Study": "string",
            "Years Attended": "string"
        }}
    ],
    "Work Experience": [
        {{
            "Position": "string",
            "Company Name": "string",
            "Years Worked": "string",
            "Achievements": "string"
        }}
    ],
    "Certifications": [
        "cert1",
        "cert2"
    ]
}}

Important rules:

- Extract only information that appears in the resume.
- Do not invent information.
- If information is not available, use "N/A".
- Skills should be returned as an array of strings.
- Work experience should preserve the candidate's actual positions and companies.
- Return ONLY JSON.
- Do not include Markdown.
- Do not include explanations before or after the JSON.

Resume Text:
{text[:4000]}
"""

        # ----------------------------------------------------
        # Gemini request payload
        # ----------------------------------------------------
        data = {
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
                "temperature": 1.0,
                "maxOutputTokens": 2000
            }
        }

        # ----------------------------------------------------
        # Send request
        # ----------------------------------------------------
        print("🔄 Sending resume to Gemini...")

        response = requests.post(
            GEMINI_API_URL,
            headers=HEADERS,
            json=data,
            timeout=60
        )

        # ----------------------------------------------------
        # Print detailed error from Gemini
        # ----------------------------------------------------
        if not response.ok:

            print(
                f"❌ Gemini API Error: "
                f"{response.status_code}"
            )

            print("Gemini response:")

            try:
                print(
                    json.dumps(
                        response.json(),
                        indent=2
                    )
                )
            except Exception:
                print(response.text)

            response.raise_for_status()

        # ----------------------------------------------------
        # Parse Gemini response
        # ----------------------------------------------------
        response_data = response.json()

        candidates = response_data.get(
            "candidates",
            []
        )

        if not candidates:
            raise ValueError(
                "Gemini returned no candidates"
            )

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
                "Gemini returned no response parts"
            )

        message_content = parts[0].get(
            "text",
            ""
        ).strip()

        if not message_content:
            raise ValueError(
                "Gemini returned an empty response"
            )

        # ----------------------------------------------------
        # Extract structured JSON
        # ----------------------------------------------------
        structured = extract_json_from_response(
            message_content
        )

        # ----------------------------------------------------
        # Validate structure
        # ----------------------------------------------------
        if not isinstance(structured, dict):
            raise ValueError(
                "Gemini response is not a JSON object"
            )

        # Make sure expected fields exist
        structured.setdefault(
            "Full Name",
            "N/A"
        )

        structured.setdefault(
            "Contact Information",
            {
                "email": "N/A",
                "phone": "N/A"
            }
        )

        structured.setdefault(
            "Skills",
            []
        )

        structured.setdefault(
            "Education",
            []
        )

        structured.setdefault(
            "Work Experience",
            []
        )

        structured.setdefault(
            "Certifications",
            []
        )

        # ----------------------------------------------------
        # Add original resume text
        # ----------------------------------------------------
        structured["Raw Text"] = text

        print(
            f"✅ Resume parsed successfully: "
            f"{structured.get('Full Name', 'N/A')}"
        )

        return structured

    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except requests.exceptions.HTTPError as e:

        print(
            f"❌ API request error in "
            f"parse_resume_with_llm_binary: {e}"
        )

        print(
            f"❌ GEMINI_API_KEY configured: "
            f"{'Yes' if GEMINI_API_KEY else 'No'}"
        )

        return create_default_response(text)

    except requests.exceptions.Timeout as e:

        print(
            f"❌ Gemini request timed out: {e}"
        )

        return create_default_response(text)

    except requests.exceptions.RequestException as e:

        print(
            f"❌ Gemini API connection error: {e}"
        )

        print(
            f"❌ GEMINI_API_KEY configured: "
            f"{'Yes' if GEMINI_API_KEY else 'No'}"
        )

        return create_default_response(text)

    except fitz.fitz.FileDataError as e:

        print(
            f"❌ PDF parsing error in "
            f"parse_resume_with_llm_binary: {e}"
        )

        return create_default_response("")

    except ValueError as e:

        print(
            f"❌ Resume parsing error: {e}"
        )

        return create_default_response(text)

    except json.JSONDecodeError as e:

        print(
            f"❌ JSON decoding error: {e}"
        )

        return create_default_response(text)

    except Exception as e:

        print(
            f"❌ Unexpected error in "
            f"parse_resume_with_llm_binary: {e}"
        )

        print(
            f"❌ Error type: {type(e).__name__}"
        )

        return create_default_response(text)


# ============================================================
# DEFAULT RESPONSE
# ============================================================

def create_default_response(text=""):
    """
    Create default response structure when resume
    parsing fails.
    """

    return {
        "Full Name": "N/A",

        "Contact Information": {
            "email": "N/A",
            "phone": "N/A"
        },

        "Skills": [],

        "Education": [],

        "Work Experience": [],

        "Certifications": [],

        "Raw Text": text
    }
