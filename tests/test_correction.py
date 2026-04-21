"""
Tests for the correction module.
Mocks both Claude and Gemma engines — no API calls during CI.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from src.correction import correct_dictation, CorrectionResult, DictationError


ONE_ERROR_RESPONSE = {
    "score": 90,
    "total_words": 10,
    "errors": [
        {
            "wrong": "maison",
            "correct": "maisons",
            "type": "spelling",
            "explanation": "Missing plural 's' — les maisons takes a plural noun.",
        }
    ],
}

PERFECT_RESPONSE = {
    "score": 100,
    "total_words": 6,
    "errors": [],
}

ACCENT_ERROR_RESPONSE = {
    "score": 80,
    "total_words": 5,
    "errors": [
        {
            "wrong": "eleve",
            "correct": "élève",
            "type": "accent",
            "explanation": "Missing grave accents on both e's.",
        }
    ],
}


def _mock_claude(response_data: dict):
    """Patch _claude_correct to return a fixed CorrectionResult (with API key set)."""
    from src.correction import _parse_correction_json
    from unittest.mock import patch as _patch
    import contextlib

    @contextlib.contextmanager
    def _ctx():
        with _patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            with _patch(
                "src.correction._claude_correct",
                return_value=_parse_correction_json(json.dumps(response_data)),
            ):
                yield

    return _ctx()


def test_returns_correction_result():
    with _mock_claude(ONE_ERROR_RESPONSE):
        result = correct_dictation("les maison sont belles", "les maisons sont belles")
    assert isinstance(result, CorrectionResult)
    assert result.score == 90
    assert result.total_words == 10
    assert result.error_count == 1


def test_error_fields_populated():
    with _mock_claude(ONE_ERROR_RESPONSE):
        result = correct_dictation("les maison", "les maisons")
    err = result.errors[0]
    assert isinstance(err, DictationError)
    assert err.wrong == "maison"
    assert err.correct == "maisons"
    assert err.type == "spelling"
    assert "plural" in err.explanation.lower()


def test_perfect_dictation():
    with _mock_claude(PERFECT_RESPONSE):
        result = correct_dictation("le chat mange", "le chat mange")
    assert result.score == 100
    assert result.errors == []
    assert result.error_count == 0


def test_accent_error_type():
    with _mock_claude(ACCENT_ERROR_RESPONSE):
        result = correct_dictation("un eleve", "un élève")
    assert result.errors[0].type == "accent"


def test_errors_by_type_groups_correctly():
    response = {
        "score": 60,
        "total_words": 10,
        "errors": [
            {"wrong": "a", "correct": "à", "type": "accent", "explanation": "x"},
            {"wrong": "b", "correct": "bb", "type": "spelling", "explanation": "x"},
            {"wrong": "c", "correct": "cc", "type": "accent", "explanation": "x"},
        ],
    }
    with _mock_claude(response):
        result = correct_dictation("a b c", "à bb cc")
    by_type = result.errors_by_type
    assert by_type["accent"] == 2
    assert by_type["spelling"] == 1


def test_handles_markdown_wrapped_json():
    wrapped = f"```json\n{json.dumps(PERFECT_RESPONSE)}\n```"
    from src.correction import _parse_correction_json
    result = _parse_correction_json(wrapped)
    assert result.score == 100


def test_falls_back_to_gemma_when_no_credits():
    """When ANTHROPIC_API_KEY is absent, Gemma fallback is used."""
    import os
    from src.correction import _parse_correction_json
    gemma_result = _parse_correction_json(json.dumps(PERFECT_RESPONSE))

    env_without_key = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    with patch.dict("os.environ", env_without_key, clear=True):
        with patch("src.correction._gemma_correct", return_value=gemma_result):
            result = correct_dictation("le chat", "le chat")
    assert result.score == 100
