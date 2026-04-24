"""
FinSight v2 — config/ai_client.py
================================
Free AI Router — 100% free, no credit card needed.

Tries Groq (llama3-8b-8192) first for speed.
Falls back to Google Gemini (gemini-1.5-flash) if Groq hits rate limits or fails.
"""

import os
import json
import re
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.1-8b-instant"

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
GEMINI_MODEL   = "gemini-1.5-flash"

# ─────────────────────────────────────────────────────────────
# GROQ CLIENT
# ─────────────────────────────────────────────────────────────
def ask_groq(prompt: str, system: str = "", temperature: float = 0.1) -> str:
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = requests.post(
        GROQ_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        },
        json={
            "model":       GROQ_MODEL,
            "messages":    messages,
            "temperature": temperature,
            "max_tokens":  2048,
        },
        timeout=20,
    )
    
    if response.status_code != 200:
        raise RuntimeError(f"Groq API returned {response.status_code}: {response.text}")
        
    return response.json()["choices"][0]["message"]["content"].strip()


# ─────────────────────────────────────────────────────────────
# GEMINI CLIENT (FALLBACK)
# ─────────────────────────────────────────────────────────────
def ask_gemini(prompt: str, system: str = "", temperature: float = 0.1) -> str:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    # For simple REST generation content, append the system prompt.
    full_prompt = f"System Instruction:\n{system}\n\nUser Prompt:\n{prompt}" if system else prompt
    
    response = requests.post(
        f"{GEMINI_API_URL}?key={api_key}",
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 2048,
            }
        },
        timeout=20,
    )
    
    if response.status_code != 200:
        raise RuntimeError(f"Gemini API returned {response.status_code}: {response.text}")
        
    data = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        raise RuntimeError(f"Unexpected Gemini response format: {data}")


# ─────────────────────────────────────────────────────────────
# AI ROUTER & JSON WRAPPER
# ─────────────────────────────────────────────────────────────
def ask_ai_json(prompt: str, system: str = "") -> dict:
    """
    Tries Groq first. If it fails (e.g. rate limit / no key), falls back to Gemini.
    Parses the response as JSON.
    """
    raw = None
    last_error = ""

    # 1. Try Groq
    try:
        raw = ask_groq(prompt, system, temperature=0.1)
    except Exception as e:
        last_error = f"Groq Error: {str(e)}"
        
        # 2. Fallback to Gemini
        try:
            raw = ask_gemini(prompt, system, temperature=0.1)
        except Exception as e2:
            raise RuntimeError(f"AI Router Failed! Both APIs failed.\n{last_error}\nGemini Error: {str(e2)}")

    if not raw:
        raise RuntimeError("AI Router returned empty response")

    # Strip markdown fences
    cleaned = re.sub(r"```(?:json)?\s*|```", "", raw).strip()
    
    # Extract first JSON block if model added explanation text
    json_block = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
    if json_block:
        cleaned = json_block.group(0)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as de:
        raise ValueError(f"Failed to parse JSON: {de}\nRaw AI Output: {cleaned}")


# ─────────────────────────────────────────────────────────────
# HEALTH / STATUS
# ─────────────────────────────────────────────────────────────
def ai_status() -> dict:
    """Returns status of both Groq and Gemini configurations."""
    groq_key = os.environ.get("GROQ_API_KEY", "")
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    
    return {
        "router": "Groq → Gemini Fallback",
        "groq": {
            "configured": bool(groq_key),
            "model": GROQ_MODEL,
        },
        "gemini": {
            "configured": bool(gemini_key),
            "model": GEMINI_MODEL,
        }
    }
