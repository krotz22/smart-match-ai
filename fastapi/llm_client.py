import os
import time

import requests
from dotenv import load_dotenv

# Load variables from a local .env file (on Render, set them in the dashboard)
load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.mistral.ai/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "mistral-small-latest")

if not LLM_API_KEY:
    print("⚠️ WARNING: LLM_API_KEY not found in environment variables")


def call_llm(prompt, temperature=0.3, max_tokens=4096, retries=3, timeout=90):
    """
    Send a prompt to an OpenAI-compatible chat endpoint (Mistral by default)
    and return the reply text. Expects the model to answer with a JSON object.

    Retries on timeouts and on 429 / 5xx responses.
    Raises requests exceptions on failure so callers can handle them.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY or ''}",
    }

    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }

    response = None

    for attempt in range(retries):
        try:
            response = requests.post(
                f"{LLM_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=timeout,
            )
        except requests.exceptions.Timeout:
            if attempt == retries - 1:
                raise
            time.sleep(10 * (attempt + 1))
            continue

        if response.status_code in (429, 500, 502, 503):
            if attempt < retries - 1:
                time.sleep(10 * (attempt + 1))
                continue

        break

    if not response.ok:
        print(f"❌ LLM API Error: {response.status_code}")
        print(response.text)
        response.raise_for_status()

    data = response.json()

    choices = data.get("choices") or []
    if not choices:
        raise ValueError("LLM returned no choices")

    content = (choices[0].get("message", {}).get("content") or "").strip()

    if not content:
        raise ValueError("LLM returned an empty response")

    return content
