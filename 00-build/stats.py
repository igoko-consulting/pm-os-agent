"""Read the run ledger and print what Cortex has actually been doing.

The eval lifecycle in 05-bounds-evals §4 names production traces as the stage that
measures accuracy over time rather than at a point. The ledger is that hook: it is
structured, it is written at every exit, and it holds ids, counts and enums only, so
none of this needs the drafts to be kept.

    python stats.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

LEDGER = Path(__file__).parent / "run-output" / "run-ledger.json"


def main() -> None:
    if not LEDGER.exists():
        print("No ledger yet. Run the agent once.")
        return
    rows = json.loads(LEDGER.read_text(encoding="utf-8"))
    n = len(rows)
    costs = sorted(r.get("cost_usd", 0.0) for r in rows)
    validated = [r for r in rows if r.get("critic_verdict")]
    rejected = [r for r in validated if r["critic_verdict"] == "fail"]
    blocked = [r for r in rows if r.get("guards_fired")]

    print(f"Runs: {n}   spend: ${sum(costs):.4f}   "
          f"mean ${sum(costs)/n:.4f}   median ${costs[n // 2]:.4f}   max ${costs[-1]:.4f}")
    print(f"Reached a human: {sum(1 for r in rows if r.get('outcome') == 'accepted')}/{n}")

    print("\nExits")
    for exit_type, count in Counter(r.get("exit", "unknown") for r in rows).most_common():
        print(f"  {exit_type:22} {count:3}  {count / n:5.0%}")

    print("\nValidation")
    if validated:
        print(f"  reached the critic      {len(validated):3}  {len(validated) / n:5.0%}")
        print(f"  rejected                {len(rejected):3}  {len(rejected) / len(validated):5.0%} of validated")
        for model, count in Counter(r["critic_model"] for r in validated).most_common():
            spend = sum(r["cost_usd"] for r in validated if r["critic_model"] == model)
            print(f"  {model:22} {count:3}  ${spend:.4f}")
        failed = Counter(c for r in validated for c in r.get("checks_failed", []))
        if failed:
            print("  checks failed:", ", ".join(f"#{c} x{n_}" for c, n_ in failed.most_common()))
    else:
        print("  no run has reached the critic yet")

    print("\nGuards")
    if blocked:
        for code, count in Counter(c for r in blocked for c in r["guards_fired"]).most_common():
            print(f"  {code:22} {count:3}")
    else:
        print(f"  never fired in {n} runs")

    reviewed = [r for r in rows if r.get("human_verdict")]
    print("\nHuman review")
    if reviewed:
        approved = sum(1 for r in reviewed if r["human_verdict"] == "approved")
        reached = sum(1 for r in rows if r.get("outcome") == "accepted")
        print(f"  reviewed                {len(reviewed):3}  of {reached} that reached a human")
        print(f"  approved without edit   {approved:3}  {approved / len(reviewed):5.0%}")
        for verdict, count in Counter(r["human_verdict"] for r in reviewed).most_common():
            if verdict != "approved":
                print(f"  {verdict:22} {count:3}")
        reasons = Counter(r["human_reason"] for r in reviewed if r.get("human_reason"))
        if reasons:
            print("  reasons:", ", ".join(f"{k} x{v}" for k, v in reasons.most_common()))
    else:
        print("  no run has been reviewed yet. Every ROI metric depends on this.")

    repeats = Counter((r["project_id"], r["iso_week"]) for r in rows)
    dupes = {k: v for k, v in repeats.items() if v > 1}
    if dupes:
        print("\nRepeat runs in one ISO week (the dedupe rule allows one)")
        for (pid, week), count in sorted(dupes.items(), key=lambda kv: -kv[1]):
            print(f"  {pid:12} {week}  {count} runs")


if __name__ == "__main__":
    main()
