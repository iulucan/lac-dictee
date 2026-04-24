"""
OCR module — extracts text from handwritten dictation images and scanned PDFs.

Priority:
  1. Claude Vision (claude-haiku-4-5) — best for handwriting, fast
  2. Infinity-Parser-7B via HuggingFace Space — free, excellent on scanned docs
  3. Tesseract — last resort, poor on handwriting
PDF support: PyMuPDF converts PDF pages to images for Tesseract path.
"""

import os
import base64
import io
import tempfile
from dataclasses import dataclass

import anthropic
import fitz  # PyMuPDF
import pytesseract
from gradio_client import Client, handle_file
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
- IGNORE all teacher marks: checkmarks (✓), crosses (✗ ×), underlines, circles, grades, and red/green ink
- IGNORE any text written by the teacher: margin notes, inline corrections, words added above/below student lines
- IGNORE lined paper, pencil guidelines, and watermarks
- If a word is illegible, write [?] in its place
- Output ONLY the student's original text, nothing else\
"""

import unicodedata as _unicodedata

_HF_SPACE = "infly/infinity-parser"
_HF_MODEL = "Infinity-Parser-7B"


def _is_annotation_char(c: str) -> bool:
    """True if a character looks like a teacher mark (checkmark, cross, ballot)."""
    cp = ord(c)
    if cp in (0xFE0F, 0xFE0E):        # variation selectors
        return True
    if 0x2700 <= cp <= 0x27BF:        # Dingbats block (covers ✓✔✗✘ and many more)
        return True
    if cp in (0x2705, 0x274C, 0x274E, 0x2612, 0x2611, 0x2610, 0x00D7, 0x00F7):
        return True
    try:
        name = _unicodedata.name(c, "")
        return any(kw in name for kw in ("CHECK", "BALLOT", "CROSS MARK"))
    except Exception:
        return False


def _strip_teacher_annotations(text: str) -> str:
    """Remove teacher checkmarks and annotation-only lines from OCR output."""
    cleaned = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            cleaned.append(line)
            continue
        # Drop lines made entirely of annotation marks (e.g. "✓", "✓ et originaux")
        if _is_annotation_char(stripped[0]):
            continue
        # Strip inline annotation characters from otherwise normal lines
        cleaned_line = "".join(c for c in line if not _is_annotation_char(c))
        cleaned.append(cleaned_line)
    return "\n".join(cleaned).strip()


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
        if pix.samples.count(b"\xff") > len(pix.samples) * 0.98:
            continue  # skip blank pages
        pages.append(pix.tobytes("png"))
    return pages


def _claude_vision_ocr(raw_bytes: bytes) -> OCRResult:
    """Use Claude Vision to transcribe handwritten French text (image or PDF)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set.")

    client = anthropic.Anthropic(api_key=api_key)

    if _is_pdf(raw_bytes):
        b64 = base64.standard_b64encode(raw_bytes).decode("utf-8")
        content = [
            {
                "type": "document",
                "source": {"type": "base64", "media_type": "application/pdf", "data": b64},
            },
            {"type": "text", "text": "Transcribe the handwritten French dictation in this document."},
        ]
    else:
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

    text = _strip_teacher_annotations(message.content[0].text.strip())
    illegible_count = text.count("[?]")
    word_count = max(len(text.split()), 1)
    confidence = max(0.0, 1.0 - illegible_count / word_count)

    warning = ""
    if illegible_count > 0:
        warning = f"{illegible_count} illegible word(s) marked as [?]. Review the extracted text."

    return OCRResult(text=text, confidence=confidence, warning=warning)


def _infinity_parser_ocr(raw_bytes: bytes) -> OCRResult:
    """Use Infinity-Parser-7B via HuggingFace Space (free, no API key needed)."""
    suffix = ".pdf" if _is_pdf(raw_bytes) else ".png"

    # If image, convert to PNG for the Space
    if not _is_pdf(raw_bytes):
        image = Image.open(io.BytesIO(raw_bytes))
        image = ImageOps.exif_transpose(image)
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        raw_bytes = buf.getvalue()

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(raw_bytes)
        tmp_path = tmp.name

    try:
        client = Client(_HF_SPACE, verbose=False)
        result = client.predict(
            doc_path=handle_file(tmp_path),
            prompt="Please convert the document into Markdown format.",
            model_id=_HF_MODEL,
            api_name="/doc_parser",
        )
        text = result[1].strip()
        # Strip markdown code fences if present
        lines = text.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    finally:
        os.unlink(tmp_path)

    if not text:
        raise ValueError("Infinity-Parser returned empty result.")

    illegible_count = text.count("[?]")
    word_count = max(len(text.split()), 1)
    confidence = max(0.0, 1.0 - illegible_count / word_count)

    return OCRResult(text=text, confidence=confidence, warning="")


def preprocess_image(image: Image.Image) -> Image.Image:
    return _preprocess_image(image)


def _preprocess_image(image: Image.Image) -> Image.Image:
    image = image.convert("L")
    image = ImageOps.autocontrast(image, cutoff=2)
    image = image.filter(ImageFilter.SHARPEN)
    image = ImageEnhance.Contrast(image).enhance(1.8)
    return image


def _tesseract_ocr(image: Image.Image) -> OCRResult:
    """Last-resort Tesseract OCR."""
    try:
        data = pytesseract.image_to_data(
            image, lang="fra", output_type=pytesseract.Output.DICT
        )
    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract is not installed. macOS: brew install tesseract tesseract-lang"
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

    warning = "Low OCR confidence — please review the extracted text carefully." if avg_conf < 0.5 else ""
    return OCRResult(text=text, confidence=avg_conf, warning=warning)


def _tesseract_pdf_ocr(raw_bytes: bytes) -> OCRResult:
    """Tesseract last-resort for PDFs: render each page then OCR."""
    page_images = _pdf_to_images(raw_bytes)
    if not page_images:
        return OCRResult(text="", confidence=0.0, warning="PDF appears to be blank.")

    all_texts, all_confs = [], []
    for png_bytes in page_images:
        image = Image.open(io.BytesIO(png_bytes))
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        result = _tesseract_ocr(_preprocess_image(image))
        if result.text:
            all_texts.append(result.text)
            all_confs.append(result.confidence)

    text = "\n".join(all_texts).strip()
    avg_conf = (sum(all_confs) / len(all_confs)) if all_confs else 0.0
    warning = "Low OCR confidence on scanned PDF — please review carefully." if avg_conf < 0.5 else ""
    return OCRResult(text=text, confidence=avg_conf, warning=warning)


def extract_text_from_image(file) -> OCRResult:
    """
    Extract French text from an uploaded image or PDF file.

    Tries engines in priority order:
      1. Claude Vision  — best quality, requires ANTHROPIC_API_KEY + credits
      2. Infinity-Parser-7B (HF Space) — free, great on scanned docs/photos
      3. Tesseract — last resort

    Args:
        file: Streamlit UploadedFile or file-like object (jpg/jpeg/png/pdf)

    Returns:
        OCRResult with extracted text, confidence, and optional warning.
    """
    raw_bytes = file.read() if hasattr(file, "read") else file
    is_pdf = _is_pdf(raw_bytes)

    # 1. Claude Vision
    _claude_skip_reason = ""
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return _claude_vision_ocr(raw_bytes)
        except anthropic.BadRequestError as e:
            if "credit balance" in str(e):
                _claude_skip_reason = "💳 Anthropic API credits exhausted — add credits at console.anthropic.com/billing."
            else:
                _claude_skip_reason = f"Claude Vision error: {e}"
        except Exception as e:
            _claude_skip_reason = f"Claude Vision unavailable: {e}"
    else:
        _claude_skip_reason = "ANTHROPIC_API_KEY not set."

    # 2. Infinity-Parser-7B
    try:
        return _infinity_parser_ocr(raw_bytes)
    except Exception as _inf_err:
        _inf_fail = str(_inf_err)

    # 3. Tesseract (last resort)
    warning_prefix = (
        f"⚠️ {_claude_skip_reason} "
        "Falling back to Tesseract OCR (poor handwriting support). "
    )
    if is_pdf:
        result = _tesseract_pdf_ocr(raw_bytes)
    else:
        image = Image.open(io.BytesIO(raw_bytes))
        image = ImageOps.exif_transpose(image)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        result = _tesseract_ocr(_preprocess_image(image))

    result.warning = (warning_prefix + result.warning).strip()
    return result
