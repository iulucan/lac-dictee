"""
Annotation module — generates visual error markup from correction results.

Level 1: HTML annotated text (Streamlit display)
Level 2: Annotated image (Pillow rendered, teacher red-pen style)
"""

import io
import re
from PIL import Image, ImageDraw, ImageFont
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
