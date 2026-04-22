"""
Annotation module — generates visual error markup from correction results.

Level 1: HTML annotated text (Streamlit display)
Level 2: Annotated image (Pillow rendered, teacher red-pen style)
"""

import io
import re
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageDraw, ImageFont, ImageOps
from src.correction import CorrectionResult

_ERROR_COLORS = {
    "spelling":     "#e74c3c",   # red
    "grammar":      "#e67e22",   # orange
    "accent":       "#f1c40f",   # yellow
    "missing_word": "#3498db",   # blue
    "extra_word":   "#9b59b6",   # purple
}

_DEFAULT_COLOR = "#e74c3c"

_LEGEND = {
    "spelling":     "Spelling",
    "grammar":      "Grammar",
    "accent":       "Accent",
    "missing_word": "Missing word",
    "extra_word":   "Extra word",
}


def _tokenize(text: str) -> list[tuple[str, str]]:
    """Split text into (token, whitespace) pairs, preserving newlines."""
    tokens = []
    for line in text.splitlines():
        parts = re.split(r"(\s+)", line)
        for part in parts:
            if part:
                tokens.append(part)
        tokens.append("\n")
    return tokens


def _build_error_map(errors) -> dict[str, tuple[str, str]]:
    """Build {wrong_word: (correct_word, error_type)} mapping."""
    error_map = {}
    for err in errors:
        key = err.wrong.strip().lower()
        error_map[key] = (err.correct, err.type)
    return error_map


def generate_annotated_html(student_text: str, correction: CorrectionResult) -> str:
    """
    Generate HTML markup of the student text with errors highlighted.
    Wrong words: red strikethrough + correct word in green.
    """
    if not correction.errors:
        return f"<p style='font-size:16px;line-height:2'>{student_text}</p>"

    error_map = _build_error_map(correction.errors)
    tokens = _tokenize(student_text)

    html_parts = ["<p style='font-size:16px;line-height:2.4;font-family:monospace'>"]
    used = set()

    for token in tokens:
        if token == "\n":
            html_parts.append("<br>")
            continue

        clean = re.sub(r"[^\w''-]", "", token).lower()
        if clean in error_map and clean not in used:
            correct, etype = error_map[clean]
            color = _ERROR_COLORS.get(etype, _DEFAULT_COLOR)
            label = _LEGEND.get(etype, etype)
            html_parts.append(
                f'<span title="{label}" style="color:{color};text-decoration:line-through">{token}</span>'
                f'<sup style="color:#27ae60;font-size:11px;margin-left:2px"><b>{correct}</b></sup> '
            )
            used.add(clean)
        else:
            html_parts.append(f"{token} ")

    html_parts.append("</p>")

    # Legend
    if correction.errors:
        html_parts.append("<div style='margin-top:8px;font-size:12px'>")
        for etype, color in _ERROR_COLORS.items():
            if any(e.type == etype for e in correction.errors):
                html_parts.append(
                    f'<span style="background:{color};color:white;padding:2px 6px;'
                    f'border-radius:3px;margin-right:6px">{_LEGEND[etype]}</span>'
                )
        html_parts.append("</div>")

    return "".join(html_parts)


def generate_annotated_image(student_text: str, correction: CorrectionResult) -> bytes:
    """
    Render an annotated image (teacher red-pen style) using Pillow.

    - Wrong words: red strikethrough
    - Correct word: green text above the line
    - Returns PNG bytes
    """
    # ── Fonts ────────────────────────────────────────────────────────────────
    font_size = 28
    small_size = 20
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", small_size)
        font_bold = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except Exception:
        font = ImageFont.load_default()
        font_small = font
        font_bold = font

    error_map = _build_error_map(correction.errors)

    # ── Layout pass: calculate required height ───────────────────────────────
    margin = 40
    line_height = font_size + 30   # extra space for correction text above
    col_width = 900
    lines = student_text.splitlines()

    # Measure each line width (approximate)
    img_width = col_width + margin * 2
    img_height = margin * 2 + len(lines) * line_height + 60  # +60 for header

    # ── Draw ─────────────────────────────────────────────────────────────────
    img = Image.new("RGB", (img_width, img_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Header
    draw.text((margin, margin // 2), "Annotated Correction", font=font_bold, fill=(80, 80, 80))
    draw.line([(margin, margin + 4), (img_width - margin, margin + 4)], fill=(200, 200, 200), width=1)

    y = margin + 20
    used = set()

    for line in lines:
        x = margin
        words = line.split(" ")

        for word in words:
            clean = re.sub(r"[^\w''-]", "", word).lower()
            color = _ERROR_COLORS.get(
                error_map[clean][1] if clean in error_map else "", _DEFAULT_COLOR
            )

            if clean in error_map and clean not in used:
                correct, etype = error_map[clean]
                err_color = _ERROR_COLORS.get(etype, _DEFAULT_COLOR)

                # Correct word above in green
                draw.text((x, y - small_size - 4), correct, font=font_small, fill=(39, 174, 96))

                # Wrong word in error color
                draw.text((x, y), word, font=font, fill=err_color)

                # Strikethrough
                bbox = draw.textbbox((x, y), word, font=font)
                mid_y = (bbox[1] + bbox[3]) // 2
                draw.line([(bbox[0], mid_y), (bbox[2], mid_y)], fill=err_color, width=2)

                word_w = bbox[2] - bbox[0]
                used.add(clean)
            else:
                draw.text((x, y), word, font=font, fill=(30, 30, 30))
                bbox = draw.textbbox((x, y), word, font=font)
                word_w = bbox[2] - bbox[0]

            x += word_w + 10  # word spacing

        y += line_height

    # ── Legend ───────────────────────────────────────────────────────────────
    y += 10
    draw.line([(margin, y), (img_width - margin, y)], fill=(200, 200, 200), width=1)
    y += 8
    lx = margin
    for etype, color in _ERROR_COLORS.items():
        if any(e.type == etype for e in correction.errors):
            label = _LEGEND[etype]
            # Color swatch
            draw.rectangle([lx, y + 4, lx + 14, y + 18], fill=color)
            draw.text((lx + 18, y), label, font=font_small, fill=(60, 60, 60))
            lx += len(label) * 10 + 36

    buf = io.BytesIO()
    img.save(buf, format="PNG", dpi=(150, 150))
    return buf.getvalue()


def _load_image_from_bytes(image_bytes: bytes) -> Image.Image:
    """Load image from raw bytes — supports JPEG, PNG, and PDF."""
    if image_bytes[:4] == b"%PDF":
        import fitz
        doc = fitz.open(stream=image_bytes, filetype="pdf")
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            if pix.samples.count(b"\xff") <= len(pix.samples) * 0.98:
                return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        raise ValueError("PDF appears blank.")
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return ImageOps.exif_transpose(img)


def _get_word_boxes_opencv(img_pil: Image.Image) -> list[dict]:
    """
    Detect word bounding boxes using OpenCV contour analysis.
    Does NOT read text — only finds visual word regions.

    Returns list of {x, y, w, h} dicts sorted in reading order.
    """
    img_np = np.array(img_pil)
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

    # Isolate the paper from the background using Otsu's auto-threshold.
    # Works for phone photos (dark table behind paper) and flat scans alike.
    img_area = img_pil.width * img_pil.height
    _, bright = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    bg_cnts, _ = cv2.findContours(bright, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    paper_mask = np.zeros_like(gray)
    largest = max(bg_cnts, key=cv2.contourArea) if bg_cnts else None
    if largest is not None and cv2.contourArea(largest) > img_area * 0.25:
        cv2.drawContours(paper_mask, [largest], -1, 255, -1)
        # Erode inward: removes paper-edge contrast that looks like ink
        margin_px = max(20, min(img_pil.width, img_pil.height) // 60)
        paper_mask = cv2.erode(paper_mask, np.ones((margin_px, margin_px), np.uint8))
    else:
        paper_mask[:] = 255  # flat scan or no clear paper boundary — use full image

    # Adaptive threshold isolates ink strokes on paper
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 31, 10
    )

    # Remove isolated noise pixels (salt from paper texture)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    # Apply paper mask — background noise disappears
    thresh = cv2.bitwise_and(thresh, thresh, mask=paper_mask)

    # Dilate horizontally to merge chars → words
    kw = max(15, img_pil.width // 35)
    kh = max(3, img_pil.height // 200)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kw, kh))
    dilated = cv2.dilate(thresh, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # Filter: too small (noise) or too large (full-line/page artifact)
        if w < 15 or h < 8 or w * h > img_area * 0.05 or w / h > 25:
            continue
        boxes.append({"x": x, "y": y, "w": w, "h": h})

    # Cluster into lines by Y centre, then sort left→right within each line
    if not boxes:
        return []

    line_gap = max(b["h"] for b in boxes) * 0.8
    boxes.sort(key=lambda b: b["y"])

    lines: list[list[dict]] = []
    current_line: list[dict] = [boxes[0]]
    for box in boxes[1:]:
        if abs(box["y"] - current_line[-1]["y"]) < line_gap:
            current_line.append(box)
        else:
            lines.append(sorted(current_line, key=lambda b: b["x"]))
            current_line = [box]
    lines.append(sorted(current_line, key=lambda b: b["x"]))

    return [box for line in lines for box in line]


def overlay_annotations_on_image(
    image_bytes: bytes,
    student_text: str,
    correction: CorrectionResult,
) -> bytes:
    """
    Overlay error annotations directly on the original handwritten image.

    Strategy:
    1. OpenCV contour detection → word bounding boxes (position only, no OCR)
    2. Align boxes with Infinity-Parser words by reading order index
    3. Draw red box + strikethrough on errors, green correction above

    Returns PNG bytes of the annotated original image.
    """
    img = _load_image_from_bytes(image_bytes)

    # ── OpenCV word boxes ─────────────────────────────────────────────────────
    boxes = _get_word_boxes_opencv(img)

    # ── Align with student text words by index ────────────────────────────────
    ip_words = [w for w in re.split(r"\s+", student_text.replace("\n", " ")) if w]
    word_to_box = {idx: boxes[idx] for idx in range(min(len(ip_words), len(boxes)))}

    # ── Map errors to word positions ──────────────────────────────────────────
    error_map = _build_error_map(correction.errors)
    error_positions = []
    used = set()
    for idx, word in enumerate(ip_words):
        clean = re.sub(r"[^\w''-]", "", word).lower()
        if clean in error_map and idx not in used and idx in word_to_box:
            correct, etype = error_map[clean]
            error_positions.append((word_to_box[idx], correct, etype))
            used.add(idx)

    # ── Draw annotations ──────────────────────────────────────────────────────
    draw = ImageDraw.Draw(img)
    font_size = max(20, img.width // 55)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except Exception:
        font = ImageFont.load_default()

    lw = max(2, img.width // 600)  # line width scales with image

    for box, correct, etype in error_positions:
        x, y, w, h = box["x"], box["y"], box["w"], box["h"]
        c_hex = _ERROR_COLORS.get(etype, _DEFAULT_COLOR)
        color = tuple(int(c_hex[i:i+2], 16) for i in (1, 3, 5))

        # Coloured rectangle
        draw.rectangle([x - 2, y - 2, x + w + 2, y + h + 2], outline=color, width=lw)

        # Strikethrough
        mid_y = y + h // 2
        draw.line([(x, mid_y), (x + w, mid_y)], fill=color, width=lw + 1)

        # Green correction above
        draw.text((x, max(0, y - font_size - 4)), correct, font=font, fill=(39, 174, 96))

    # ── Legend ────────────────────────────────────────────────────────────────
    legend_h = 40
    legend = Image.new("RGB", (img.width, legend_h), (245, 245, 245))
    ld = ImageDraw.Draw(legend)
    try:
        lf = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
    except Exception:
        lf = ImageFont.load_default()

    lx = 16
    for etype, c_hex in _ERROR_COLORS.items():
        if any(e.type == etype for e in correction.errors):
            color = tuple(int(c_hex[i:i+2], 16) for i in (1, 3, 5))
            ld.rectangle([lx, 12, lx + 14, 26], fill=color)
            label = _LEGEND[etype]
            ld.text((lx + 18, 10), label, font=lf, fill=(60, 60, 60))
            lx += len(label) * 10 + 36

    combined = Image.new("RGB", (img.width, img.height + legend_h), (255, 255, 255))
    combined.paste(img, (0, 0))
    combined.paste(legend, (0, img.height))

    buf = io.BytesIO()
    combined.save(buf, format="PNG", dpi=(150, 150))
    return buf.getvalue()
