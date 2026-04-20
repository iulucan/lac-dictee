"""
OCR module — extracts text from handwritten dictation images.

System requirement:
  macOS:  brew install tesseract tesseract-lang
  Ubuntu: sudo apt install tesseract-ocr tesseract-ocr-fra
"""

import pytesseract
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import io
from dataclasses import dataclass


@dataclass
class OCRResult:
    text: str
    confidence: float  # 0.0 – 1.0, estimated from Tesseract data
    warning: str = ""


def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Improve OCR accuracy on handwritten text:
    1. Grayscale — removes colour noise
    2. Auto-contrast — normalises uneven lighting from phone photos
    3. Sharpen — improves edge definition of handwritten strokes
    4. Contrast boost — increases ink/paper separation
    """
    image = image.convert("L")
    image = ImageOps.autocontrast(image, cutoff=2)
    image = image.filter(ImageFilter.SHARPEN)
    image = ImageEnhance.Contrast(image).enhance(1.8)
    return image


def extract_text_from_image(file) -> OCRResult:
    """
    Extract French text from an uploaded image file.

    Args:
        file: Streamlit UploadedFile (jpg/jpeg/png) or file-like object

    Returns:
        OCRResult with extracted text, confidence estimate, and optional warning.

    Raises:
        RuntimeError: if tesseract is not installed or French pack is missing.
    """
    raw_bytes = file.read() if hasattr(file, "read") else file
    image = Image.open(io.BytesIO(raw_bytes))

    # Convert RGBA/P (PNG with transparency) to RGB before grayscale
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    image = preprocess_image(image)

    # lang='fra' is required for French — ensures accented characters
    # (é, è, ê, à, â, ù, û, ü, ï, ô, œ, æ, ç) are recognised correctly.
    try:
        data = pytesseract.image_to_data(
            image,
            lang="fra",
            output_type=pytesseract.Output.DICT,
        )
    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract is not installed. "
            "macOS: brew install tesseract tesseract-lang | "
            "Ubuntu: sudo apt install tesseract-ocr tesseract-ocr-fra"
        )

    # Build text and calculate mean confidence from non-empty words
    words = []
    confidences = []
    for i, word in enumerate(data["text"]):
        word = word.strip()
        if word:
            words.append(word)
            conf = int(data["conf"][i])
            if conf > 0:
                confidences.append(conf)

    text = " ".join(words).strip()
    avg_conf = (sum(confidences) / len(confidences) / 100) if confidences else 0.0

    warning = ""
    if avg_conf < 0.5:
        warning = (
            "Low OCR confidence. The image may be blurry or the handwriting hard to read. "
            "Please review the extracted text carefully."
        )

    return OCRResult(text=text, confidence=avg_conf, warning=warning)
