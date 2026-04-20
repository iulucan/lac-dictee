"""
Correction module — uses Claude AI to compare student text vs correct text
and return a structured error report.
"""

import os
import json
import anthropic

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


SYSTEM_PROMPT = """You are an expert French language teacher.
You receive two texts:
1. The student's text (extracted via OCR from handwriting — may contain OCR artifacts)
2. The correct reference text

Your job is to compare them word by word and identify every error.

Respond ONLY with valid JSON in this exact format:
{
  "score": <integer 0-100>,
  "total_words": <integer>,
  "errors": [
    {
      "wrong": "<what the student wrote>",
      "correct": "<what it should be>",
      "type": "<spelling|grammar|accent|missing_word|extra_word>",
      "explanation": "<short explanation in English>"
    }
  ]
}

Rules:
- Score = 100 - (errors / total_words * 100), minimum 0
- Ignore minor OCR artifacts that are clearly not student mistakes
- Be strict about French accents (é vs e = accent error)
- Do not include any text outside the JSON object"""


def correct_dictation(student_text: str, correct_text: str) -> dict:
    """
    Compare student's dictation against the correct text using Claude.

    Args:
        student_text: OCR-extracted text from student's handwriting
        correct_text: The original correct dictation text

    Returns:
        dict with keys: score (int), total_words (int), errors (list)
    """
    client = _get_client()

    user_message = f"""STUDENT TEXT:
{student_text}

CORRECT TEXT:
{correct_text}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = message.content[0].text.strip()

    # Strip markdown code fences if Claude wraps the JSON
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw)
