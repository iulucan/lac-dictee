"""
Demo batch script — 8 Champignons (A1) + 8 Renaissance (A2) students.

Saves all corrections to SQLite so analytics dashboard shows full class data.
PDFs saved to reports/demo/

Usage:
    .venv/bin/python3 batch_demo.py
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from src.ocr import extract_text_from_image
from src.correction import correct_dictation
from src.pdf_export import generate_pdf
from src.storage import save_correction

CHAMP_DIR  = Path("../DataBaseLacDictee/Champignons")
RENA_DIR   = Path("../DataBaseLacDictee/Renaissance")
REPORT_DIR = Path("reports/demo")

CHAMP_REF = (CHAMP_DIR / "champignons_reference.txt").read_text(encoding="utf-8").strip()
RENA_REF  = (RENA_DIR  / "renaissance_reference.txt").read_text(encoding="utf-8").strip()

# Prepend exercise label as first line → analytics groups by this
CHAMP_TEXT = "DemoExercise_A1\n" + CHAMP_REF
RENA_TEXT  = "DemoExercise_A2\n" + RENA_REF

EXERCISES = [
    {
        "label": "DemoExercise_A1 (Champignons)",
        "correct_text": CHAMP_TEXT,
        "jpgs": sorted(CHAMP_DIR.glob("IMG_*.JPG")),
    },
    {
        "label": "DemoExercise_A2 (Renaissance)",
        "correct_text": RENA_TEXT,
        "jpgs": sorted(RENA_DIR.glob("IMG_*.JPG")),
    },
]

REPORT_DIR.mkdir(parents=True, exist_ok=True)


def process_student(jpg: Path, correct_text: str, student_name: str, ex_label: str) -> dict:
    print(f"\n  [{ex_label}] {student_name} — {jpg.name}")

    # OCR
    print("    OCR ... ", end="", flush=True)
    with open(jpg, "rb") as f:
        ocr = extract_text_from_image(f)
    print(f"done ({ocr.confidence:.0%})")

    # Correction
    print("    AI correction ... ", end="", flush=True)
    correction = correct_dictation(ocr.text, correct_text)
    print(f"score {correction.score}/100  errors {correction.error_count}")

    # Save to SQLite
    save_correction(correction, student_name, correct_text, ocr.text)

    # PDF
    try:
        pdf_bytes = generate_pdf(correction, student_name, correct_text)
        pdf_path = REPORT_DIR / f"{ex_label.split()[0]}_{student_name}_report.pdf"
        pdf_path.write_bytes(pdf_bytes)
        print(f"    PDF → {pdf_path}")
    except Exception as e:
        print(f"    PDF error (skipped): {e}")

    return {"student": student_name, "score": correction.score, "errors": correction.error_count}


def main():
    results = {}
    for ex in EXERCISES:
        jpgs = ex["jpgs"]
        if len(jpgs) != 8:
            print(f"WARNING: expected 8 JPGs for {ex['label']}, found {len(jpgs)}")
        results[ex["label"]] = []
        print(f"\n{'='*60}")
        print(f"  {ex['label']}  ({len(jpgs)} students)")
        print(f"{'='*60}")
        for i, jpg in enumerate(jpgs, 1):
            r = process_student(jpg, ex["correct_text"], f"Student_{i}", ex["label"])
            results[ex["label"]].append(r)

    # Summary
    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}")
    for ex_label, rows in results.items():
        scores = [r["score"] for r in rows]
        print(f"\n  {ex_label}")
        for r in rows:
            bar = "█" * (r["score"] // 10)
            print(f"    {r['student']:<12} {r['score']:>3}/100  {bar}")
        print(f"    {'─'*30}")
        print(f"    Class avg:  {sum(scores)/len(scores):.0f}/100")
    print()


if __name__ == "__main__":
    main()
