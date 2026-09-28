"""Record what the human thought of a run.

The ledger recorded everything Cortex did and nothing about whether the draft was
any good, so every ROI metric in 06-autonomy/production-and-autonomy.md had no data
behind it: approved without edit, cost per approved update, trust incidents. All
three need a verdict from the person at the checkpoint.

Verdicts are an enum, and the optional reason is a code, not free text. The ledger
is the only store Cortex owns and the PII constraint in 04-memory-context §5 holds.

    python review.py P-NORTH approved
    python review.py P-NORTH corrected --reason wrong_figure
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

LEDGER = Path(__file__).parent / "run-output" / "run-ledger.json"
VERDICTS = ("approved", "edited", "corrected", "discarded")
REASONS = ("wrong_figure", "wrong_status", "missing_context", "tone", "stale_proposal", "other")


def main() -> None:
    ap = argparse.ArgumentParser(description="Attach a human verdict to the latest run.")
    ap.add_argument("project_id")
    ap.add_argument("verdict", choices=VERDICTS)
    ap.add_argument("--reason", choices=REASONS, default=None,
                    help="only meaningful for edited / corrected")
    args = ap.parse_args()

    if not LEDGER.exists():
        raise SystemExit("No ledger yet. Run the agent first.")
    rows = json.loads(LEDGER.read_text(encoding="utf-8"))
    mine = [r for r in rows if r.get("project_id") == args.project_id]
    if not mine:
        raise SystemExit(f"No runs recorded for {args.project_id}.")

    row = mine[-1]
    row["human_verdict"] = args.verdict
    if args.reason:
        row["human_reason"] = args.reason
    LEDGER.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")

    print(f"{row.get('run_id', 'run')}  {args.project_id}  {args.verdict}"
          + (f"  ({args.reason})" if args.reason else ""))
    reviewed = [r for r in rows if r.get("human_verdict")]
    approved = [r for r in reviewed if r["human_verdict"] == "approved"]
    if reviewed:
        print(f"Approved without edit: {len(approved)}/{len(reviewed)} reviewed "
              f"({len(approved) / len(reviewed):.0%})")


if __name__ == "__main__":
    main()
