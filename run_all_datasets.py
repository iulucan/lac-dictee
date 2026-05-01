"""
Run LacDictée pipeline on all available datasets and print a summary table.
Usage: .venv/bin/python3 run_all_datasets.py
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from src.ocr import extract_text_from_image
from src.correction import correct_dictation
from src.pdf_export import generate_pdf

DB = Path("/Users/user/Desktop/PC/GitHub/DataBaseLacDictee")
REPORTS = Path(__file__).parent / "reports"
REPORTS.mkdir(exist_ok=True)

DATASETS = [
    {
        "name": "Champignons dans la rue (A1 – TV5Monde)",
        "folder": DB / "Champignons",
        "reference": DB / "Champignons" / "champignons_reference.txt",
        "extensions": [".jpg", ".jpeg", ".png", ".pdf"],
        "skip": ["reference", "corrigée", "tv5monde"],
    },
    {
        "name": "Le génie de la Renaissance (A2 – TV5Monde)",
        "folder": DB / "Renaissance",
        "reference": DB / "Renaissance" / "renaissance_reference.txt",
        "extensions": [".jpg", ".jpeg", ".png", ".pdf"],
        "skip": ["reference", "corrigée", "tv5monde"],
    },
    {
        "name": "Dictée 2 – Les jardinières (Enfants)",
        "folder": DB / "Enfants_LaDictee_Sample",
        "reference": DB / "Reference_Sample" / "enfants_dictee2_reference.txt",
        "extensions": [".jpg", ".jpeg", ".png"],
        "skip": [],
    },
]

SUMMARY = []


def safe_name(path: Path) -> str:
    return path.stem.replace(" ", "_").replace("(", "").replace(")", "").replace(".", "_")


def process_file(filepath: Path, reference_text: str, dataset_name: str, student_label: str):
    try:
        with open(filepath, "rb") as f:
            ocr = extract_text_from_image(f)

        if not ocr.text.strip():
            return {"student": student_label, "dataset": dataset_name,
                    "score": "—", "errors": "—", "status": "OCR empty", "file": filepath.name}

        correction = correct_dictation(ocr.text, reference_text)

        pdf_bytes = generate_pdf(correction, student_label, reference_text)
        out_path = REPORTS / f"{safe_name(filepath)}_report.pdf"
        out_path.write_bytes(pdf_bytes)

        return {
            "student": student_label,
            "dataset": dataset_name,
            "score": correction.score,
            "errors": correction.error_count,
            "top_errors": [f"{e.wrong}→{e.correct}" for e in correction.errors[:3]],
            "status": "✅",
            "file": filepath.name,
            "report": out_path.name,
        }
    except Exception as e:
        return {"student": student_label, "dataset": dataset_name,
                "score": "—", "errors": "—", "status": f"❌ {str(e)[:60]}", "file": filepath.name}


def collect_files(cfg):
    folder = cfg["folder"]
    exts = set(e.lower() for e in cfg["extensions"])
    skip_kw = [s.lower() for s in cfg["skip"]]
    files = []
    for f in sorted(folder.iterdir()):
        if f.suffix.lower() not in exts:
            continue
        if any(kw in f.name.lower() for kw in skip_kw):
            continue
        files.append(f)
    return files


print(f"\n{'='*70}")
print(f"  LacDictée — Full Dataset Run   {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"{'='*70}\n")

total_files = 0
for cfg in DATASETS:
    files = collect_files(cfg)
    ref_text = Path(cfg["reference"]).read_text(encoding="utf-8").strip()
    dataset_name = cfg["name"]

    print(f"\n📁 {dataset_name}")
    print(f"   Reference: {Path(cfg['reference']).name}")
    print(f"   Students:  {len(files)} files")
    print(f"   {'Student':<28} {'Score':>6} {'Errors':>7}  {'Top Mistakes'}")
    print(f"   {'-'*65}")

    for i, fp in enumerate(files, 1):
        label = f"Student_{i:02d}"
        result = process_file(fp, ref_text, dataset_name, label)
        SUMMARY.append(result)
        total_files += 1
        score_str = f"{result['score']}/100" if isinstance(result['score'], int) else result['score']
        err_str = str(result['errors']) if isinstance(result['errors'], int) else result['errors']
        top = ", ".join(result.get("top_errors", [])) if result.get("top_errors") else result["status"]
        print(f"   {label:<28} {score_str:>6} {err_str:>7}  {top}")

print(f"\n{'='*70}")
print(f"  SUMMARY")
print(f"{'='*70}")

scored = [r for r in SUMMARY if isinstance(r['score'], int)]
failed = [r for r in SUMMARY if not isinstance(r['score'], int)]

print(f"\n  Total papers processed : {total_files}")
print(f"  Successfully scored    : {len(scored)}")
print(f"  Failed / OCR empty     : {len(failed)}")

if scored:
    avg = sum(r['score'] for r in scored) / len(scored)
    print(f"  Average score         : {avg:.1f}/100")
    print(f"  Score range           : {min(r['score'] for r in scored)} – {max(r['score'] for r in scored)}/100")
    print(f"  Total errors found    : {sum(r['errors'] for r in scored)}")

print(f"\n  Reports saved to: {REPORTS}")

# Save JSON summary
summary_path = REPORTS / "run_summary.json"
summary_path.write_text(json.dumps(SUMMARY, ensure_ascii=False, indent=2))
print(f"  JSON summary: {summary_path.name}")
print()
