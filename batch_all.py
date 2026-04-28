"""
Process all remaining student dictation files and generate PDF reports.
Usage: .venv/bin/python3 batch_all.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from batch_correct import process

DB = Path("../DataBaseLacDictee")

JOBS = [
    # --- Les Fêtes de fin d'année ---
    (DB / "Sample_Dictee_1.jpg",  DB / "fetes_fin_annee_reference.txt",  "Fetes_Ogrenci_1"),
    (DB / "Sample_Dictee_2.jpg",  DB / "fetes_fin_annee_reference.txt",  "Fetes_Ogrenci_2"),

    # --- Carnaval et Pâques ---
    (DB / "Sample_Dictee_3.jpg",  DB / "carnaval_paques_reference.txt",  "Carnaval_Ogrenci_1"),

    # --- Enfants Dictée 2 (17 students) ---
    *[
        (
            DB / "Enfants_LaDictee_Samples" / f"Sample_Dictee_Enfants{i}.jpeg",
            DB / "enfants_dictee2_reference.txt",
            f"Enfants_Ogrenci_{i:02d}",
        )
        for i in range(1, 18)
    ],
]

if __name__ == "__main__":
    ok, fail = 0, 0
    for student_path, ref_path, name in JOBS:
        try:
            process(str(student_path), str(ref_path), name)
            ok += 1
        except Exception as e:
            print(f"\n❌ {name}: {e}")
            fail += 1

    print(f"\n{'='*60}")
    print(f"Done: {ok} reports generated, {fail} failed.")
    print(f"Reports saved to: lac-dictee/reports/")
