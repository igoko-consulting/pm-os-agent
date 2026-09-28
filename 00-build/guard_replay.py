"""Replay every recorded draft through the safety guards.

The guards block a run, so the risk that matters is a false positive on a good
draft: a human pulled in for nothing, which is how people stop trusting an agent.
They cannot be tested by waiting for them to fire in live running, because they are
a backstop for the model failing to refuse and the model mostly does not.

Only m4-* and m5-* traces are replayed. Earlier ones ran on the pre-data-pack
fixtures, so their figures (#812, 41%) are genuinely absent from today's tool
results and the uncited-figure guard would flag them correctly but uselessly.

    python guard_replay.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from agent import guard_violations  # noqa: E402
import tools  # noqa: E402

TRACES = Path(__file__).parent.parent / "06-autonomy" / "traces"


def name_of(pid: str) -> str:
    return tools.get_project(pid).get("name", pid).split(" (")[0]


def advanced(text: str) -> bool:
    """Did this run reach the guards at all?

    Guards run only on the done path. An escalation that lists embargoed project ids
    in order to ask which one was meant never reaches them, and counting it as a
    block over-reports the false-positive rate.
    """
    return not any(marker in text for marker in
                   ("ESCALATED by Cortex", "STUCK,", "BOUND TRIPPED", "MAX ITERATIONS",
                    "KILL SWITCH", "BLOCKED,"))


def draft_of(text: str) -> str:
    if "PROPOSED OUTPUT:" not in text:
        return ""
    return text.split("PROPOSED OUTPUT:")[-1].split("=" * 64)[0]


def main() -> None:
    files = sorted(f for f in TRACES.glob("m[45]-*.txt"))
    if not files:
        print("No current-era traces found.")
        return

    flagged = 0
    for f in files:
        text = f.read_text(encoding="utf-8")
        draft = draft_of(text)
        if not draft.strip():
            print(f"{f.name:38} no draft in this trace, nothing to replay")
            continue
        if not advanced(text):
            print(f"{f.name:38} halted before the guards, not replayed")
            continue
        match = re.search(r"\bP-[A-Z]+\b", text)
        pid = match.group(0) if match else "unknown"
        # Rebuild the evidence from the fixtures, not from the trace: printed tool
        # results are truncated at 300 chars for display.
        log = [f"get_activity({{'project_id': '{pid}'}}) -> {json.dumps(tools.get_activity(pid))}",
               f"get_project -> {json.dumps(tools.get_project(pid))}",
               # Query by name: the corpus is keyed on project name, not id, so
               # searching "P-NORTH" returns nothing and every past figure looks uncited.
               f"search_past_updates -> {json.dumps(tools.search_past_updates(name_of(pid)))}",
               f"get_roadmap -> {json.dumps(tools.get_roadmap(pid))}"]
        hits = guard_violations(draft, log, pid)
        if hits:
            flagged += 1
            print(f"{f.name:38} BLOCKED  {'; '.join(code for code, _ in hits)}")
            for _, msg in hits:
                print(f"{'':38}          {msg}")
        else:
            print(f"{f.name:38} clean")

    print(f"\n{flagged} of {len(files)} recorded drafts would be blocked today.")
    print("Traces recorded before the 2026-07-06 data pack cite figures that no longer exist\n"
          "in the fixtures, so a block on #812, #815 or 39% is the guard working against today's\n"
          "data rather than a false positive.")


if __name__ == "__main__":
    main()
