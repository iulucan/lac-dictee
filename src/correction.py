"""
Correction module — uses Claude AI to compare student text vs correct text
and return a structured error report with explanations.
"""

import os
import json
import anthropic
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


_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Add it to your .env file."
            )
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


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


def correct_dictation(student_text: str, correct_text: str) -> CorrectionResult:
    """
    Compare student's dictation against the correct reference using Claude.

    Args:
        student_text: OCR-extracted text from the student's handwriting
        correct_text: The teacher's original correct dictation text

    Returns:
        CorrectionResult with score, total_words, and list of DictationError objects.

    Raises:
        RuntimeError: if ANTHROPIC_API_KEY is not set
        ValueError: if Claude returns malformed JSON
    """
    client = _get_client()

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"STUDENT TEXT:\n{student_text}\n\n"
                    f"CORRECT TEXT:\n{correct_text}"
                ),
            }
        ],
    )

    raw = message.content[0].text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude returned invalid JSON: {e}\nRaw response: {raw[:200]}")

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


def reconstruct_reference(ocr_text: str) -> str:
    """
    Ask Claude to reconstruct the likely correct French text from noisy OCR output.
    Used when the teacher does not have the original reference text.

    Returns the reconstructed text as a plain string.
    """
    client = _get_client()

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=_RECONSTRUCT_PROMPT,
        messages=[{"role": "user", "content": f"OCR TEXT:\n{ocr_text}"}],
    )

    return message.content[0].text.strip()
