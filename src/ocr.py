"""
OCR module — extracts text from handwritten dictation images.

Requires: tesseract with French language pack installed
  macOS:  brew install tesseract tesseract-lang
  Ubuntu: sudo apt install tesseract-ocr tesseract-ocr-fra
"""

import pytesseract
from PIL import Image, ImageFilter, ImageEnhance
import io


def preprocess_image(image: Image.Image) -> Image.Image:
    """Improve OCR accuracy: grayscale → sharpen → contrast boost."""
    image = image.convert("L")  # grayscale
    image = image.filter(ImageFilter.SHARPEN)
    image = ImageEnhance.Contrast(image).enhance(2.0)
    return image


def extract_text_from_image(file) -> str:
    """
    Extract French text from an uploaded image file.

    Args:
        file: Streamlit UploadedFile object (jpg/png)

    Returns:
        Extracted text string, stripped of excess whitespace.
    """
    image = Image.open(io.BytesIO(file.read()))
    image = preprocess_image(image)

    # lang='fra' is required for correct French character recognition
    # including accented letters: é, è, ê, à, â, ù, û, ü, ï, ô, œ, æ, ç
    text = pytesseract.image_to_string(image, lang="fra")

    return text.strip()
