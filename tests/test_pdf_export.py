"""Tests for src/pdf_export.py"""

from src.correction import CorrectionResult, DictationError
from src.pdf_export import generate_pdf


def _result_with_errors():
    return CorrectionResult(
        score=70,
        total_words=10,
        errors=[
            DictationError("maision", "maison", "spelling", "Wrong letters"),
            DictationError("eleve", "élève", "accent", "Missing accent"),
        ],
    )


def test_generate_pdf_returns_bytes():
    pdf = generate_pdf(_result_with_errors(), "Marie", "Le chat mange.")
    assert isinstance(pdf, bytes)
    assert len(pdf) > 100


def test_pdf_starts_with_pdf_header():
    pdf = generate_pdf(_result_with_errors(), "Marie", "Le chat mange.")
    assert pdf[:4] == b"%PDF"


def test_generate_pdf_no_errors():
    result = CorrectionResult(score=100, total_words=8, errors=[])
    pdf = generate_pdf(result, "Jean", "La maison est belle.")
    assert isinstance(pdf, bytes)
    assert len(pdf) > 100


def test_generate_pdf_empty_student_name():
    pdf = generate_pdf(_result_with_errors(), "", "Le chat mange.")
    assert isinstance(pdf, bytes)
