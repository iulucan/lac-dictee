"""
Accuracy tests — compare LacDictée output against teacher ground truth.

Runs the full pipeline (OCR → Claude correction) on real classroom dictation
images and measures how many teacher-marked errors the system finds.

Run:
    pytest tests/test_accuracy.py -v -s

Requires: ANTHROPIC_API_KEY in .env  (skipped in CI — no API key there)
"""

import json
import pytest
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).parent.parent / "data" / "testing"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_cases() -> list[dict]:
    """Return test cases that have teacher_corrections ground truth."""
    index = json.loads((DATA_DIR / "index.json").read_text())
    return [tc for tc in index if "teacher_corrections" in tc]


def _match(teacher_wrong: str, lacdictee_errors) -> bool:
    """True if teacher's 'wrong' word appears in any LacDictée error (fuzzy)."""
    tw = teacher_wrong.lower().strip()
    for err in lacdictee_errors:
        ew = err.wrong.lower().strip()
        if tw in ew or ew in tw:
            return True
    return False


def _report(case_id: str, teacher_data: dict, correction) -> dict:
    teacher_errors = teacher_data["teacher_corrections"]
    expected = teacher_data["expected_lacdictee_output"]

    matched, missed = [], []
    for tc in teacher_errors:
        (matched if _match(tc["wrong"], correction.errors) else missed).append(tc)

    recall = len(matched) / len(teacher_errors) if teacher_errors else 1.0

    return {
        "case_id":                   case_id,
        "teacher_errors":            len(teacher_errors),
        "lacdictee_errors":          correction.error_count,
        "matched":                   len(matched),
        "missed_errors":             [f"{e['wrong']} → {e['correct']} ({e['type']})" for e in missed],
        "recall":                    round(recall, 2),
        "lacdictee_score":           correction.score,
        "teacher_score_normalized":  teacher_data["meta"]["teacher_score_normalized"],
        "score_delta":               abs(correction.score - teacher_data["meta"]["teacher_score_normalized"]),
        "pass_threshold":            expected["pass_threshold"],
        "min_errors_required":       expected["min_errors_to_find"],
        "passed":                    len(matched) >= expected["min_errors_to_find"],
    }


def _print_report(r: dict) -> None:
    print(f"\n{'─' * 60}")
    print(f"  Test case : {r['case_id']}")
    print(f"  Recall    : {r['matched']}/{r['teacher_errors']} teacher errors found  ({r['recall']*100:.0f}%)")
    print(f"  Score     : LacDictée {r['lacdictee_score']}/100  vs  teacher {r['teacher_score_normalized']}/100  (Δ {r['score_delta']})")
    print(f"  Errors    : LacDictée found {r['lacdictee_errors']} total")
    if r["missed_errors"]:
        print(f"  Missed    : {', '.join(r['missed_errors'])}")
    print(f"  Result    : {'✅ PASS' if r['passed'] else '❌ FAIL'}  — {r['pass_threshold']}")
    print(f"{'─' * 60}")


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.accuracy
@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["id"])
def test_accuracy(case):
    """Full pipeline accuracy test against teacher ground truth."""
    from src.ocr import extract_text_from_image
    from src.correction import correct_dictation

    image_path = DATA_DIR / case["input_photo"]
    ref_path   = DATA_DIR / case["reference_text"]
    gt_path    = DATA_DIR / case["teacher_corrections"]

    assert image_path.exists(), f"Missing image: {image_path}"
    assert ref_path.exists(),   f"Missing reference: {ref_path}"
    assert gt_path.exists(),    f"Missing ground truth: {gt_path}"

    teacher_data = json.loads(gt_path.read_text())
    reference    = ref_path.read_text().strip()

    # ── Step 1: OCR ───────────────────────────────────────────────────────────
    print(f"\n[{case['id']}] Running OCR on {image_path.name}…")
    with open(image_path, "rb") as f:
        ocr_result = extract_text_from_image(f)

    print(f"[{case['id']}] OCR confidence: {int(ocr_result.confidence * 100)}%")
    print(f"[{case['id']}] OCR text (first 200 chars):\n{ocr_result.text[:200]}")

    assert ocr_result.text.strip(), "OCR returned empty text"

    # ── Step 2: Claude correction ─────────────────────────────────────────────
    print(f"\n[{case['id']}] Running Claude correction…")
    correction = correct_dictation(
        student_text=ocr_result.text,
        correct_text=reference,
    )

    # ── Step 3: Compare against teacher ───────────────────────────────────────
    report = _report(case["id"], teacher_data, correction)
    _print_report(report)

    assert report["passed"], (
        f"Accuracy too low for {case['id']}: "
        f"found {report['matched']}/{report['teacher_errors']} teacher errors "
        f"(need {report['min_errors_required']}). "
        f"Missed: {report['missed_errors']}"
    )
