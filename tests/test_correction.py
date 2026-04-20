"""
Tests for the correction module.
Uses a mocked Anthropic client — no API calls during CI.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from src.correction import correct_dictation, CorrectionResult, DictationError


def make_mock_client(response_data: dict):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=json.dumps(response_data))]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_msg
    return mock_client


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


@patch("src.correction._get_client")
def test_returns_correction_result(mock_get_client):
    mock_get_client.return_value = make_mock_client(ONE_ERROR_RESPONSE)
    result = correct_dictation("les maison sont belles", "les maisons sont belles")
    assert isinstance(result, CorrectionResult)
    assert result.score == 90
    assert result.total_words == 10
    assert result.error_count == 1


@patch("src.correction._get_client")
def test_error_fields_populated(mock_get_client):
    mock_get_client.return_value = make_mock_client(ONE_ERROR_RESPONSE)
    result = correct_dictation("les maison", "les maisons")
    err = result.errors[0]
    assert isinstance(err, DictationError)
    assert err.wrong == "maison"
    assert err.correct == "maisons"
    assert err.type == "spelling"
    assert "plural" in err.explanation.lower()


@patch("src.correction._get_client")
def test_perfect_dictation(mock_get_client):
    mock_get_client.return_value = make_mock_client(PERFECT_RESPONSE)
    result = correct_dictation("le chat mange", "le chat mange")
    assert result.score == 100
    assert result.errors == []
    assert result.error_count == 0


@patch("src.correction._get_client")
def test_accent_error_type(mock_get_client):
    mock_get_client.return_value = make_mock_client(ACCENT_ERROR_RESPONSE)
    result = correct_dictation("un eleve", "un élève")
    assert result.errors[0].type == "accent"


@patch("src.correction._get_client")
def test_errors_by_type_groups_correctly(mock_get_client):
    response = {
        "score": 60,
        "total_words": 10,
        "errors": [
            {"wrong": "a", "correct": "à", "type": "accent", "explanation": "x"},
            {"wrong": "b", "correct": "bb", "type": "spelling", "explanation": "x"},
            {"wrong": "c", "correct": "cc", "type": "accent", "explanation": "x"},
        ],
    }
    mock_get_client.return_value = make_mock_client(response)
    result = correct_dictation("a b c", "à bb cc")
    by_type = result.errors_by_type
    assert by_type["accent"] == 2
    assert by_type["spelling"] == 1


@patch("src.correction._get_client")
def test_handles_markdown_wrapped_json(mock_get_client):
    wrapped = f"```json\n{json.dumps(PERFECT_RESPONSE)}\n```"
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=wrapped)]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_msg
    mock_get_client.return_value = mock_client

    result = correct_dictation("le chat", "le chat")
    assert result.score == 100
