"""
Tests for the OCR module.
Uses a mocked pytesseract to avoid requiring tesseract in CI.
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


@patch("src.ocr.pytesseract.image_to_data")
def test_extract_returns_ocr_result(mock_tess):
    mock_tess.return_value = MOCK_TESS_DATA
    file = io.BytesIO(make_test_image())
    result = extract_text_from_image(file)
    assert isinstance(result, OCRResult)
    assert "Le" in result.text
    assert result.confidence > 0


@patch("src.ocr.pytesseract.image_to_data")
def test_extract_joins_words(mock_tess):
    mock_tess.return_value = MOCK_TESS_DATA
    file = io.BytesIO(make_test_image())
    result = extract_text_from_image(file)
    assert result.text == "Le chat mange"


@patch("src.ocr.pytesseract.image_to_data")
def test_low_confidence_sets_warning(mock_tess):
    low_conf_data = {
        "text": ["abc", "def"],
        "conf": [20, 15],
    }
    mock_tess.return_value = low_conf_data
    file = io.BytesIO(make_test_image())
    result = extract_text_from_image(file)
    assert result.warning != ""
    assert result.confidence < 0.5


@patch("src.ocr.pytesseract.image_to_data")
def test_rgba_image_handled(mock_tess):
    mock_tess.return_value = MOCK_TESS_DATA
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
