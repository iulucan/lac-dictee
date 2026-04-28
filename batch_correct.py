"""
Batch correction script — process one or more student dictation files.

Usage:
    .venv/bin/python3 batch_correct.py <student_file> <reference_text_file> [student_name]

Examples:
    .venv/bin/python3 batch_correct.py \
        "../DataBaseLacDictee/Champignons sur rue.pdf" \
        "../DataBaseLacDictee/champignons_reference.txt" \
        "Etudiant_1"

Output: reports/<student_name>_report.pdf
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Make sure src/ is importable
sys.path.insert(0, str(Path(__file__).parent))

from src.ocr import extract_text_from_image
from src.correction import correct_dictation
from src.pdf_export import generate_pdf


def process(student_path: str, reference_path: str, student_name: str) -> Path:
    student_file = Path(student_path)
    if not student_file.exists():
        print(f"ERROR: File not found: {student_file}")
        sys.exit(1)

    reference_text = Path(reference_path).read_text(encoding="utf-8").strip()

    print(f"\n{'='*60}")
    print(f"Student:   {student_name}")
    print(f"File:      {student_file.name}")
    print(f"Reference: {Path(reference_path).name}")
    print(f"{'='*60}")

    # Step 1 — OCR
    print("Step 1/3  OCR ... ", end="", flush=True)
    with open(student_file, "rb") as f:
        ocr_result = extract_text_from_image(f)
    print(f"done (confidence: {ocr_result.confidence:.0%})")

    if ocr_result.warning:
        print(f"  ⚠  {ocr_result.warning}")

    print(f"\nExtracted text:\n{'-'*40}")
    print(ocr_result.text)
    print(f"{'-'*40}\n")

    # Step 2 — AI correction
    print("Step 2/3  AI correction ... ", end="", flush=True)
    correction = correct_dictation(ocr_result.text, reference_text)
    print(f"done  (score: {correction.score}/100, errors: {correction.error_count})")

    if correction.errors:
        print("\nErrors found:")
        for i, err in enumerate(correction.errors, 1):
            print(f"  {i}. '{err.wrong}' → '{err.correct}' [{err.type}]")
            print(f"     {err.explanation}")

    # Step 3 — PDF report
    print("\nStep 3/3  Generating PDF report ... ", end="", flush=True)
    output_dir = Path(__file__).parent / "reports"
    output_dir.mkdir(exist_ok=True)
    safe_name = student_name.replace(" ", "_").replace("/", "-")
    out_path = output_dir / f"{safe_name}_report.pdf"
    try:
        pdf_bytes = generate_pdf(correction, student_name, reference_text)
        out_path.write_bytes(pdf_bytes)
        print(f"saved → {out_path}")
    except Exception as pdf_err:
        print(f"⚠ PDF error: {pdf_err}")

    return out_path, correction


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    student_path = sys.argv[1]
    reference_path = sys.argv[2]
    student_name = sys.argv[3] if len(sys.argv) > 3 else Path(student_path).stem

    out = process(student_path, reference_path, student_name)
    print(f"\nReport ready: {out}")
