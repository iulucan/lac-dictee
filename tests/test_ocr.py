"""
Tests for the OCR module.
Uses mocked external engines (Tesseract, Infinity-Parser) to avoid
network calls or system dependencies in CI.
"""

import io
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
from src.ocr import extract_text_from_image, preprocess_image, OCRResult


def make_test_image(text: str = "test") -> bytes:
    """Create a minimal white PNG image for testing."""
    img = Image.new("RGB", (200, 50), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


MOCK_TESS_DATA = {
    "text": ["Le", "chat", "mange", ""],
    "conf": [90, 85, 88, -1],
}

MOCK_INFINITY_RESULT = OCRResult(text="Le chat mange", confidence=0.88, warning="")


def _patch_all_engines(mock_infinity_result=MOCK_INFINITY_RESULT):
    """Return a combined context that mocks both external OCR engines."""
    return (
        patch("src.ocr._infinity_parser_ocr", return_value=mock_infinity_result),
        patch("src.ocr.pytesseract.image_to_data"),
    )


def test_extract_returns_ocr_result():
    with patch("src.ocr._infinity_parser_ocr", return_value=MOCK_INFINITY_RESULT):
        file = io.BytesIO(make_test_image())
        result = extract_text_from_image(file)
    assert isinstance(result, OCRResult)
    assert "Le" in result.text
    assert result.confidence > 0


def test_extract_joins_words():
    with patch("src.ocr._infinity_parser_ocr", return_value=MOCK_INFINITY_RESULT):
        file = io.BytesIO(make_test_image())
        result = extract_text_from_image(file)
    assert result.text == "Le chat mange"


def test_low_confidence_sets_warning():
    low_conf = OCRResult(text="abc def", confidence=0.17, warning="Low OCR confidence.")
    with patch("src.ocr._infinity_parser_ocr", return_value=low_conf):
        file = io.BytesIO(make_test_image())
        result = extract_text_from_image(file)
    assert result.warning != ""
    assert result.confidence < 0.5


def test_falls_back_to_tesseract_when_infinity_fails():
    """When Infinity-Parser raises, Tesseract should be used."""
    with patch("src.ocr._infinity_parser_ocr", side_effect=Exception("quota exceeded")):
        with patch("src.ocr.pytesseract.image_to_data", return_value=MOCK_TESS_DATA):
            file = io.BytesIO(make_test_image())
            result = extract_text_from_image(file)
    assert isinstance(result, OCRResult)
    assert "Tesseract" in result.warning


def test_rgba_image_handled():
    with patch("src.ocr._infinity_parser_ocr", return_value=MOCK_INFINITY_RESULT):
        img = Image.new("RGBA", (200, 50), color=(255, 255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        result = extract_text_from_image(buf)
    assert isinstance(result, OCRResult)


def test_preprocess_returns_grayscale():
    img = Image.new("RGB", (100, 50), color=(200, 180, 160))
    processed = preprocess_image(img)
    assert processed.mode == "L"
