"""
Process all 8 Champignons + 8 Renaissance student papers and save analytics JSON.
Files sorted by modification time (oldest = Student 1).
Usage: .venv/bin/python3 batch_tv5monde.py
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv()

from batch_correct import process

DB = Path("../DataBaseLacDictee")


def sorted_by_mtime(folder: Path) -> list[Path]:
    files = [f for f in folder.iterdir() if f.suffix.upper() == ".JPG"]
    return sorted(files, key=lambda p: p.stat().st_mtime)


champ_files = sorted_by_mtime(DB / "Champignons")
rena_files  = sorted_by_mtime(DB / "Renaissance")

JOBS = (
    [(f, DB / "Champignons" / "champignons_reference.txt", f"Champignons_Student_{i+1:02d}", "Champignons")
     for i, f in enumerate(champ_files)]
    +
    [(f, DB / "Renaissance" / "renaissance_reference.txt", f"Renaissance_Student_{i+1:02d}", "Renaissance")
     for i, f in enumerate(rena_files)]
)


if __name__ == "__main__":
    print(f"Jobs: {len(JOBS)} students total\n")

    summary = {"Champignons": [], "Renaissance": []}
    ok, fail = 0, 0

    for student_path, ref_path, name, exercise in JOBS:
        try:
            _, correction = process(str(student_path), str(ref_path), name)
            ok += 1
        except Exception as e:
            print(f"\n❌ {name}: {e}")
            fail += 1
            correction = None

        if correction is not None:
            summary[exercise].append({
                "name": name,
                "score": correction.score,
                "error_count": correction.error_count,
                "total_words": correction.total_words,
                "errors_by_type": correction.errors_by_type,
                "errors": [
                    {"wrong": e.wrong, "correct": e.correct,
                     "type": e.type, "explanation": e.explanation}
                    for e in correction.errors
                ],
            })

    # Save analytics JSON
    out_json = Path(__file__).parent / "reports" / "analytics.json"
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nAnalytics saved → {out_json}")

    print(f"\n{'='*60}")
    print(f"Done: {ok} reports generated, {fail} failed.")
