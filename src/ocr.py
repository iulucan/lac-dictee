"""
OCR module — extracts text from handwritten dictation images and scanned PDFs.

Primary: Claude Vision (claude-haiku-4-5) — handles handwriting accurately.
Fallback: Tesseract (requires brew install tesseract tesseract-lang on macOS).
PDF support: PyMuPDF converts PDF pages to images before OCR.
"""

import os
import base64
import io
from dataclasses import dataclass

import anthropic
import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageFilter, ImageEnhance, ImageOps


@dataclass
class OCRResult:
    text: str
    confidence: float  # 0.0 – 1.0
    warning: str = ""


_VISION_PROMPT = """\
You are transcribing a student's handwritten French dictation from a photo or scanned document.

Rules:
- Transcribe EXACTLY what the student wrote, including spelling mistakes and missing accents
- Do not correct any errors — the teacher needs to see the student's actual mistakes
- Ignore lined paper, margins, pencil marks not part of the text
- If a word is illegible, write [?] in its place
- Output ONLY the transcribed text, nothing else\
"""


def _is_pdf(raw_bytes: bytes) -> bool:
    return raw_bytes[:4] == b"%PDF"


def _pdf_to_images(raw_bytes: bytes, dpi: int = 200) -> list[bytes]:
    """Render each non-blank PDF page as a PNG byte string."""
    doc = fitz.open(stream=raw_bytes, filetype="pdf")
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pages = []
    for page in doc:
        pix = page.get_pixmap(matrix=mat)
        # Skip blank pages (almost all white)
        if pix.samples.count(b"\xff") > len(pix.samples) * 0.98:
            continue
        pages.append(pix.tobytes("png"))
    return pages


def _claude_vision_ocr(raw_bytes: bytes) -> OCRResult:
    """Use Claude Vision to transcribe handwritten French text (image or PDF)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set.")

    client = anthropic.Anthropic(api_key=api_key)

    if _is_pdf(raw_bytes):
        # Send PDF as document — Claude API natively supports PDFs
        b64 = base64.standard_b64encode(raw_bytes).decode("utf-8")
        content = [
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": b64,
                },
            },
            {"type": "text", "text": "Transcribe the handwritten French dictation in this document."},
        ]
    else:
        # Image: detect JPEG vs PNG
        if raw_bytes[:3] == b"\xff\xd8\xff":
            media_type = "image/jpeg"
        elif raw_bytes[:8] == b"\x89PNG\r\n\x1a\n":
            media_type = "image/png"
        else:
            media_type = "image/jpeg"

        b64 = base64.standard_b64encode(raw_bytes).decode("utf-8")
        content = [
            {
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": b64},
            },
            {"type": "text", "text": "Transcribe this handwritten French dictation."},
        ]

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=_VISION_PROMPT,
        messages=[{"role": "user", "content": content}],
    )

    text = message.content[0].text.strip()
    illegible_count = text.count("[?]")
    word_count = max(len(text.split()), 1)
    confidence = max(0.0, 1.0 - illegible_count / word_count)

    warning = ""
    if illegible_count > 0:
        warning = f"{illegible_count} illegible word(s) marked as [?]. Review the extracted text."

    return OCRResult(text=text, confidence=confidence, warning=warning)


def preprocess_image(image: Image.Image) -> Image.Image:
    return _preprocess_image(image)


def _preprocess_image(image: Image.Image) -> Image.Image:
    image = image.convert("L")
    image = ImageOps.autocontrast(image, cutoff=2)
    image = image.filter(ImageFilter.SHARPEN)
    image = ImageEnhance.Contrast(image).enhance(1.8)
    return image


def _tesseract_ocr(image: Image.Image) -> OCRResult:
    """Fallback Tesseract OCR for French text."""
    try:
        data = pytesseract.image_to_data(
            image,
            lang="fra",
            output_type=pytesseract.Output.DICT,
        )
    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract is not installed. "
            "macOS: brew install tesseract tesseract-lang"
        )

    words, confidences = [], []
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


def _tesseract_pdf_ocr(raw_bytes: bytes) -> OCRResult:
    """Tesseract fallback for PDFs: render each page and OCR."""
    page_images = _pdf_to_images(raw_bytes)
    if not page_images:
        return OCRResult(text="", confidence=0.0, warning="PDF appears to be blank.")

    all_texts, all_confs = [], []
    for png_bytes in page_images:
        image = Image.open(io.BytesIO(png_bytes))
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image = _preprocess_image(image)
        result = _tesseract_ocr(image)
        if result.text:
            all_texts.append(result.text)
            all_confs.append(result.confidence)

    combined_text = "\n".join(all_texts).strip()
    avg_conf = (sum(all_confs) / len(all_confs)) if all_confs else 0.0

    warning = ""
    if avg_conf < 0.5:
        warning = (
            "Low OCR confidence on scanned PDF. "
            "Please review the extracted text carefully."
        )

    return OCRResult(text=combined_text, confidence=avg_conf, warning=warning)


def extract_text_from_image(file) -> OCRResult:
    """
    Extract French text from an uploaded image or PDF file.

    Tries Claude Vision first (accurate on handwriting).
    Falls back to Tesseract if the API key is unavailable.
    Supports JPEG, PNG, and scanned PDF files.

    Args:
        file: Streamlit UploadedFile or file-like object (jpg/jpeg/png/pdf)

    Returns:
        OCRResult with extracted text, confidence estimate, and optional warning.
    """
    raw_bytes = file.read() if hasattr(file, "read") else file
    is_pdf = _is_pdf(raw_bytes)

    vision_warning = ""
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return _claude_vision_ocr(raw_bytes)
        except anthropic.BadRequestError as e:
            if "credit balance" in str(e):
                vision_warning = "Claude Vision unavailable (no API credits). Using Tesseract — review text carefully."
        except Exception:
            pass

    # Tesseract fallback
    if is_pdf:
        result = _tesseract_pdf_ocr(raw_bytes)
    else:
        image = Image.open(io.BytesIO(raw_bytes))
        image = ImageOps.exif_transpose(image)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image = _preprocess_image(image)
        result = _tesseract_ocr(image)

    if vision_warning:
        result.warning = f"{vision_warning} {result.warning}".strip()
    return result
