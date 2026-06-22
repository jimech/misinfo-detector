"""
evaluate.py
------------
Runs the labeled test set through the pipeline and reports metrics:
  - overall accuracy
  - accuracy per verdict type
  - a confusion matrix (what gets confused for what)

This is kept (not a throwaway test) so you can re-run evaluation
anytime, e.g. after changing the corpus or tuning thresholds.

Run with:   python -m src.evaluate
"""

import json
from pathlib import Path
from collections import defaultdict

from src.verifier import verify_claim
from src.retrieval_service import get_evidence_for_claim
from src.schemas import Verdict

_TESTSET_PATH = Path(__file__).resolve().parent.parent / "data" / "testset.json"

# The three possible verdicts, as plain strings, for building the matrix.
_VERDICTS = ["supported", "contradicted", "not_enough_evidence"]


def _load_testset():
    with open(_TESTSET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate():
    testset = _load_testset()

    total = len(testset)
    correct = 0

    # Count correct/total per expected verdict.
    per_verdict_total = defaultdict(int)
    per_verdict_correct = defaultdict(int)

    # Confusion matrix: confusion[expected][predicted] = count.
    confusion = {v: defaultdict(int) for v in _VERDICTS}

    # Store wrong cases to print as failure analysis.
    mistakes = []

    print(f"Evaluating {total} claims...\n")

    for row in testset:
        claim = row["claim"]
        expected = row["expected"]

        # Run the claim through retrieve -> verify.
        evidence = get_evidence_for_claim(claim, top_k=3)
        verdict, confidence, _ = verify_claim(claim, evidence)
        predicted = verdict.value

        # Tally.
        per_verdict_total[expected] += 1
        confusion[expected][predicted] += 1

        if predicted == expected:
            correct += 1
            per_verdict_correct[expected] += 1
        else:
            mistakes.append((claim, expected, predicted, confidence))

    # --- Overall accuracy --------------------------------------------
    accuracy = correct / total if total else 0.0
    print("=" * 60)
    print(f"OVERALL ACCURACY: {correct}/{total} = {accuracy:.0%}")
    print("=" * 60)

    # --- Per-verdict accuracy ----------------------------------------
    print("\nAccuracy by verdict type:")
    for v in _VERDICTS:
        t = per_verdict_total[v]
        c = per_verdict_correct[v]
        if t > 0:
            print(f"  {v:<22} {c}/{t} = {c/t:.0%}")
        else:
            print(f"  {v:<22} (none in test set)")

    # --- Confusion matrix --------------------------------------------
    print("\nConfusion matrix (rows = expected, cols = predicted):")
    header = "expected \\ predicted".ljust(22) + "".join(v[:12].ljust(14) for v in _VERDICTS)
    print("  " + header)
    for exp in _VERDICTS:
        row_str = exp.ljust(22) + "".join(
            str(confusion[exp][pred]).ljust(14) for pred in _VERDICTS
        )
        print("  " + row_str)

    # --- Failure analysis --------------------------------------------
    if mistakes:
        print(f"\n{len(mistakes)} mistakes (failure analysis):")
        for claim, exp, pred, conf in mistakes:
            print(f"  • \"{claim}\"")
            print(f"      expected={exp}, got={pred} (confidence {conf:.2f})")
    else:
        print("\nNo mistakes on this test set. 🎉")

    return accuracy


if __name__ == "__main__":
    evaluate()