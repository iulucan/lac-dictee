"""Tests for src/storage.py"""

import os
import pytest
from pathlib import Path
from src.correction import CorrectionResult, DictationError
from src.storage import save_correction, list_corrections, get_correction, DB_PATH


@pytest.fixture(autouse=True)
def clean_db():
    """Remove test DB before and after each test."""
    if DB_PATH.exists():
        DB_PATH.unlink()
    yield
    if DB_PATH.exists():
        DB_PATH.unlink()


def _result():
    return CorrectionResult(
        score=80,
        total_words=10,
        errors=[DictationError("maision", "maison", "spelling", "Wrong letters")],
    )


def test_save_returns_id():
    rid = save_correction(_result(), "Marie", "Le chat mange.", "Le chat manje.")
    assert isinstance(rid, int)
    assert rid == 1


def test_list_corrections_empty():
    assert list_corrections() == []


def test_save_and_list():
    save_correction(_result(), "Marie", "Le chat mange.", "Le chat manje.")
    records = list_corrections()
    assert len(records) == 1
    assert records[0].student_name == "Marie"
    assert records[0].score == 80


def test_list_newest_first():
    save_correction(_result(), "Alice", "Texte 1.", "Texte 1.")
    r2 = CorrectionResult(score=60, total_words=5, errors=[])
    save_correction(r2, "Bob", "Texte 2.", "Texte 2.")
    records = list_corrections()
    assert records[0].student_name == "Bob"
    assert records[1].student_name == "Alice"


def test_get_correction():
    rid = save_correction(_result(), "Marie", "Le chat mange.", "Le chat manje.")
    rec = get_correction(rid)
    assert rec is not None
    assert rec.student_name == "Marie"


def test_get_correction_not_found():
    assert get_correction(999) is None


def test_to_correction_result():
    save_correction(_result(), "Marie", "Le chat mange.", "Le chat manje.")
    rec = list_corrections()[0]
    result = rec.to_correction_result()
    assert result.score == 80
    assert result.error_count == 1
    assert result.errors[0].wrong == "maision"


def test_save_empty_student_name():
    rid = save_correction(_result(), "", "Le chat mange.", "Le chat manje.")
    rec = get_correction(rid)
    assert rec.student_name == ""
