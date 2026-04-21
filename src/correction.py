"""
Correction module — compares student text vs correct text and returns a structured
error report with explanations.

Priority:
  1. Claude (claude-sonnet-4-6)          — best quality, requires credits
  2. Groq  (llama-3.3-70b-versatile)     — free tier, fast (~1s), production
  3. Ollama (mistral local)              — free, offline, dev/local
  4. Gemma-2-9B (HuggingFace Space)      — free, last resort
"""

import os
import json
import requests
import anthropic
from groq import Groq
from gradio_client import Client
from dataclasses import dataclass, field
from typing import List


@dataclass
class DictationError:
    wrong: str
    correct: str
    type: str       # spelling | grammar | accent | missing_word | extra_word
    explanation: str


@dataclass
class CorrectionResult:
    score: int                         # 0–100
    total_words: int
    errors: List[DictationError] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def errors_by_type(self) -> dict:
        counts: dict = {}
        for e in self.errors:
            counts[e.type] = counts.get(e.type, 0) + 1
        return counts


_SYSTEM_PROMPT = """\
You are an expert French language teacher and proofreader.

You receive:
1. STUDENT TEXT — extracted via OCR from a student's handwriting (may have OCR artifacts)
2. CORRECT TEXT — the original reference dictation

Your task: compare them word by word and identify every error the student made.

Respond ONLY with valid JSON in this exact schema (no markdown, no explanation outside the JSON):
{
  "score": <integer 0-100>,
  "total_words": <integer — count of words in CORRECT TEXT>,
  "errors": [
    {
      "wrong": "<exact word or phrase the student wrote>",
      "correct": "<what it should be>",
      "type": "<spelling|grammar|accent|missing_word|extra_word>",
      "explanation": "<one-sentence explanation in English>"
    }
  ]
}

Error type definitions:
- spelling:      wrong letters (e.g. "maision" instead of "maison")
- grammar:       wrong verb form, wrong gender/number agreement
- accent:        correct letters but wrong or missing accent (e.g. "eleve" instead of "élève")
- missing_word:  student skipped a word entirely
- extra_word:    student added a word not in the original

Score formula: score = max(0, round(100 - (error_count / total_words * 100)))

Important:
- Ignore minor OCR artifacts (stray characters, punctuation noise) that are clearly not student errors
- Be strict about French accents — they are graded separately
- Do not add any text, explanation, or markdown outside the JSON object\
"""

_RECONSTRUCT_PROMPT = """\
You are a French language expert. You receive OCR-extracted text from a student's
handwritten French dictation. The OCR may have introduced errors (wrong characters,
missing accents, garbled words).

Your task: reconstruct the most likely ORIGINAL correct French dictation text.
- Fix obvious OCR artifacts (stray characters, broken words, wrong symbols)
- Restore French accents where clearly missing (é, è, ê, à, â, ù, û, ï, ô, œ, æ, ç)
- Do NOT invent new content — only clean what is clearly an OCR error
- Return ONLY the reconstructed text, no explanation, no commentary\
"""

_OLLAMA_URL = "http://localhost:11434/api/chat"
_OLLAMA_MODEL = "mistral"
_GROQ_MODEL = "llama-3.3-70b-versatile"
_HF_SPACE = "huggingface-projects/gemma-2-9b-it"


def _parse_correction_json(raw: str) -> CorrectionResult:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    brace = raw.find("{")
    if brace > 0:
        raw = raw[brace:]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}\nRaw: {raw[:300]}")
    errors = [
        DictationError(
            wrong=err.get("wrong", ""),
            correct=err.get("correct", ""),
            type=err.get("type", "spelling"),
            explanation=err.get("explanation", ""),
        )
        for err in data.get("errors", [])
    ]
    return CorrectionResult(
        score=int(data.get("score", 0)),
        total_words=int(data.get("total_words", 1)),
        errors=errors,
    )


def _user_message(student_text: str, correct_text: str) -> str:
    return f"STUDENT TEXT:\n{student_text}\n\nCORRECT TEXT:\n{correct_text}"


# ── 1. Claude ────────────────────────────────────────────────────────────────

def _claude_correct(student_text: str, correct_text: str) -> CorrectionResult:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _user_message(student_text, correct_text)}],
    )
    return _parse_correction_json(msg.content[0].text)


def _claude_reconstruct(ocr_text: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=_RECONSTRUCT_PROMPT,
        messages=[{"role": "user", "content": f"OCR TEXT:\n{ocr_text}"}],
    )
    return msg.content[0].text.strip()


# ── 2. Groq ──────────────────────────────────────────────────────────────────

def _groq_chat(system: str, user: str, max_tokens: int = 2048) -> str:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model=_GROQ_MODEL,
        max_tokens=max_tokens,
        temperature=0.1,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content


def _groq_correct(student_text: str, correct_text: str) -> CorrectionResult:
    raw = _groq_chat(_SYSTEM_PROMPT, _user_message(student_text, correct_text))
    return _parse_correction_json(raw)


def _groq_reconstruct(ocr_text: str) -> str:
    return _groq_chat(_RECONSTRUCT_PROMPT, f"OCR TEXT:\n{ocr_text}", max_tokens=512).strip()


# ── 3. Ollama ────────────────────────────────────────────────────────────────

def _ollama_available() -> bool:
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def _ollama_chat(system: str, user: str) -> str:
    payload = {
        "model": _OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    r = requests.post(_OLLAMA_URL, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["message"]["content"]


def _ollama_correct(student_text: str, correct_text: str) -> CorrectionResult:
    raw = _ollama_chat(_SYSTEM_PROMPT, _user_message(student_text, correct_text))
    return _parse_correction_json(raw)


def _ollama_reconstruct(ocr_text: str) -> str:
    return _ollama_chat(_RECONSTRUCT_PROMPT, f"OCR TEXT:\n{ocr_text}").strip()


# ── 4. Gemma (HF Space) ──────────────────────────────────────────────────────

def _gemma_chat(prompt: str, max_tokens: int = 2048) -> str:
    client = Client(_HF_SPACE, verbose=False)
    result = client.predict(
        message=prompt,
        max_new_tokens=max_tokens,
        temperature=0.1,
        api_name="/generate",
    )
    return result if isinstance(result, str) else str(result)


def _gemma_correct(student_text: str, correct_text: str) -> CorrectionResult:
    prompt = f"{_SYSTEM_PROMPT}\n\n{_user_message(student_text, correct_text)}"
    return _parse_correction_json(_gemma_chat(prompt))


def _gemma_reconstruct(ocr_text: str) -> str:
    prompt = f"{_RECONSTRUCT_PROMPT}\n\nOCR TEXT:\n{ocr_text}"
    return _gemma_chat(prompt, max_tokens=512).strip()


# ── Public API ───────────────────────────────────────────────────────────────

def correct_dictation(student_text: str, correct_text: str) -> CorrectionResult:
    """
    Compare student's dictation against the correct reference.

    Priority: Claude → Groq → Ollama → Gemma (HF Space)
    """
    # 1. Claude
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return _claude_correct(student_text, correct_text)
        except anthropic.BadRequestError as e:
            if "credit balance" not in str(e):
                raise
        except Exception:
            raise

    # 2. Groq
    if os.environ.get("GROQ_API_KEY"):
        return _groq_correct(student_text, correct_text)

    # 3. Ollama (local)
    if _ollama_available():
        return _ollama_correct(student_text, correct_text)

    # 4. Gemma (HF Space — last resort)
    return _gemma_correct(student_text, correct_text)


def reconstruct_reference(ocr_text: str) -> str:
    """
    Reconstruct the likely correct French text from noisy OCR output.

    Priority: Claude → Groq → Ollama → Gemma (HF Space)
    """
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return _claude_reconstruct(ocr_text)
        except anthropic.BadRequestError as e:
            if "credit balance" not in str(e):
                raise
        except Exception:
            raise

    if os.environ.get("GROQ_API_KEY"):
        return _groq_reconstruct(ocr_text)

    if _ollama_available():
        return _ollama_reconstruct(ocr_text)

    return _gemma_reconstruct(ocr_text)
