import io
import fitz  # PyMuPDF
import ollama
import json

def parse_resume_with_llm_binary(file_bytes: bytes):
    stream = io.BytesIO(file_bytes)
    doc = fitz.open(stream=stream, filetype="pdf")
    text = "\n".join([page.get_text() for page in doc])

    prompt = f"""
You are an expert resume parser AI.
Read the following resume and extract the following fields:
- Full Name
- Contact Information (email, phone)
- Skills (list)
- Education (Degree, Fields of Study, Years Attended)
- Work Experience (Position, Company Name, Years Worked, Achievements)
- Certifications (list)

Respond ONLY in JSON format.

Resume Text:
{text}
    """

    response = ollama.chat(
        model="mistral",
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        structured = json.loads(response['message']['content'])
        structured["Raw Text"] = text
        return structured
    except Exception as e:
        print("❌ Error parsing LLM output:", e)
        return {
            "Full Name": "N/A",
            "Contact Information": {"email": "N/A", "phone": "N/A"},
            "Skills": [],
            "Education": [],
            "Work Experience": [],
            "Certifications": [],
            "Raw Text": text
        }
