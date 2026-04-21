"""
Correction module — compares student text vs correct text and returns a structured
error report with explanations.

Priority:
  1. Claude (claude-sonnet-4-6) — best quality
  2. Gemma-2-9B via HuggingFace Space — free fallback
"""

import os
import json
import anthropic
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


_CORRECTION_PROMPT = """\
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

_HF_SPACE = "huggingface-projects/gemma-2-9b-it"


def _parse_correction_json(raw: str) -> CorrectionResult:
    """Parse JSON response into CorrectionResult. Strips markdown fences."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    # Find first { to skip any leading text
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


def _claude_correct(student_text: str, correct_text: str) -> CorrectionResult:
    """Correction via Claude (primary)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set.")

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=_CORRECTION_PROMPT,
        messages=[{
            "role": "user",
            "content": f"STUDENT TEXT:\n{student_text}\n\nCORRECT TEXT:\n{correct_text}",
        }],
    )
    return _parse_correction_json(message.content[0].text)


def _gemma_correct(student_text: str, correct_text: str) -> CorrectionResult:
    """Correction via Gemma-2-9B on HuggingFace Space (free fallback)."""
    prompt = (
        f"{_CORRECTION_PROMPT}\n\n"
        f"STUDENT TEXT:\n{student_text}\n\n"
        f"CORRECT TEXT:\n{correct_text}"
    )
    client = Client(_HF_SPACE, verbose=False)
    result = client.predict(
        message=prompt,
        max_new_tokens=2048,
        temperature=0.1,
        api_name="/generate",
    )
    raw = result if isinstance(result, str) else str(result)
    return _parse_correction_json(raw)


def correct_dictation(student_text: str, correct_text: str) -> CorrectionResult:
    """
    Compare student's dictation against the correct reference.

    Tries Claude first, falls back to Gemma-2-9B (free) if unavailable.

    Args:
        student_text: OCR-extracted text from the student's handwriting
        correct_text: The teacher's original correct dictation text

    Returns:
        CorrectionResult with score, total_words, and list of DictationError objects.
    """
    # 1. Claude (best quality)
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return _claude_correct(student_text, correct_text)
        except anthropic.BadRequestError as e:
            if "credit balance" not in str(e):
                raise
        except Exception:
            raise

    # 2. Gemma-2-9B via HuggingFace Space (free)
    return _gemma_correct(student_text, correct_text)


def reconstruct_reference(ocr_text: str) -> str:
    """
    Reconstruct the likely correct French text from noisy OCR output.
    Tries Claude first, falls back to Gemma-2-9B.
    """
    # 1. Claude
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=_RECONSTRUCT_PROMPT,
                messages=[{"role": "user", "content": f"OCR TEXT:\n{ocr_text}"}],
            )
            return message.content[0].text.strip()
        except anthropic.BadRequestError as e:
            if "credit balance" not in str(e):
                raise
        except Exception:
            raise

    # 2. Gemma fallback
    prompt = f"{_RECONSTRUCT_PROMPT}\n\nOCR TEXT:\n{ocr_text}"
    hf_client = Client(_HF_SPACE, verbose=False)
    result = hf_client.predict(
        message=prompt,
        max_new_tokens=512,
        temperature=0.1,
        api_name="/generate",
    )
    return (result if isinstance(result, str) else str(result)).strip()
