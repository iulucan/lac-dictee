"""
Tests for the correction module.

These tests use a mock Claude client to avoid API calls during CI.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.correction import correct_dictation


MOCK_RESPONSE = {
    "score": 80,
    "total_words": 10,
    "errors": [
        {
            "wrong": "maison",
            "correct": "maisons",
            "type": "spelling",
            "explanation": "Missing plural 's'",
        }
    ],
}


def make_mock_message(content: str):
    msg = MagicMock()
    msg.content = [MagicMock(text=content)]
    return msg


@patch("src.correction._get_client")
def test_correct_dictation_returns_score(mock_get_client):
    import json
    mock_client = MagicMock()
    mock_client.messages.create.return_value = make_mock_message(
        json.dumps(MOCK_RESPONSE)
    )
    mock_get_client.return_value = mock_client

    result = correct_dictation("les maison sont belles", "les maisons sont belles")

    assert result["score"] == 80
    assert len(result["errors"]) == 1
    assert result["errors"][0]["type"] == "spelling"


@patch("src.correction._get_client")
def test_perfect_dictation_no_errors(mock_get_client):
    import json
    perfect = {"score": 100, "total_words": 5, "errors": []}
    mock_client = MagicMock()
    mock_client.messages.create.return_value = make_mock_message(json.dumps(perfect))
    mock_get_client.return_value = mock_client

    result = correct_dictation("le chat mange", "le chat mange")

    assert result["score"] == 100
    assert result["errors"] == []
