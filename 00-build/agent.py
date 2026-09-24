"""Cortex, a minimal, explicit agent loop you (and your coding agent) can read end
to end. This is the agent you ship: your PM chief-of-staff. You build it by
directing your coding agent (Claude Code / Cursor / Codex) to shape this file. You
never have to hand-write it.

Every bound the course talks about is visible right here in code, not buried in a
framework: the max-iteration counter, the cost cap, the revision cap, the
stop/escalate conditions, the auto-queue cap, and the absence of any publish tool.

Usage (ask your coding agent to run these for you, or run them yourself):
    python agent.py                # runs the happy-path task (weekly status update)
    python agent.py missing-data   # the stuck/escalate case
    python agent.py jailbreak       # the prompt-injection refusal case

Every run ends by showing the drafted status update in a FINAL STATUS UPDATE block
(or LAST DRAFT, held, if a bound trips), and saves it to run-output/. That file is
always a draft held for a human, it is never posted, there is no publish tool.

Requires ANTHROPIC_API_KEY in your environment (see .env.example). Model and bounds
are read from env so you can tune them, that tuning is your M5 deliverable.

The loop is deliberately transparent (hand-written tool-calling on the anthropic
client) so a grader can see the machinery. Keep the bounds explicit if you rework it.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import anthropic

import tools
from critic import review
from prompts import CORTEX_SYSTEM

try:  # load .env if python-dotenv is installed; harmless if it isn't
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# --- Bounds (your M5 deliverable: tune these and justify them) ----------------
MODEL = os.environ.get("CORTEX_MODEL", "claude-haiku-4-5")
# The critic is the last check before a human sees anything, and it runs once per
# loop, so it is the one call worth paying more for (M1 agent-line-map anatomy).
CRITIC_MODEL = os.environ.get("CORTEX_CRITIC_MODEL", MODEL)
CRITIC_PRICE_IN = float(os.environ.get("CORTEX_CRITIC_PRICE_IN_PER_M",
                                       os.environ.get("CORTEX_PRICE_IN_PER_M", "1.00")))
CRITIC_PRICE_OUT = float(os.environ.get("CORTEX_CRITIC_PRICE_OUT_PER_M",
                                        os.environ.get("CORTEX_PRICE_OUT_PER_M", "5.00")))
MAX_ITERATIONS = int(os.environ.get("CORTEX_MAX_ITERATIONS", "8"))
MAX_REVISIONS = int(os.environ.get("CORTEX_MAX_REVISIONS", "2"))
COST_CAP_USD = float(os.environ.get("CORTEX_COST_CAP_USD", "0.50"))
MAX_QUEUE_ITEMS = int(os.environ.get("CORTEX_MAX_QUEUE_ITEMS", "10"))
# Per-response output ceiling. Required by the Messages API, and a bound in its own
# right: it caps how much any single turn can generate.
MAX_OUTPUT_TOKENS = int(os.environ.get("CORTEX_MAX_OUTPUT_TOKENS", "4096"))
# Rough $ per 1M tokens for your chosen model, set to match its pricing.
PRICE_IN = float(os.environ.get("CORTEX_PRICE_IN_PER_M", "1.00"))
PRICE_OUT = float(os.environ.get("CORTEX_PRICE_OUT_PER_M", "5.00"))

TOOL_SCHEMAS = [
    {"name": "get_project",
     "description": "Look up a project by its ID (status, flags, linked PRD).",
     "input_schema": {"type": "object", "properties": {
         "project_id": {"type": "string"}}, "required": ["project_id"]}},
    {"name": "get_activity",
     "description": "Pull recent engineering activity for a project (merged PRs, open issues, Sev-1s).",
     "input_schema": {"type": "object", "properties": {
         "project_id": {"type": "string"}}, "required": ["project_id"]}},
    {"name": "search_past_updates",
     "description": "Search previous status updates and decisions for tone and precedent.",
     "input_schema": {"type": "object", "properties": {
         "query": {"type": "string"}}, "required": []}},
    {"name": "get_roadmap",
     "description": "Return the roadmap. Some items are flagged confidential/embargoed.",
     "input_schema": {"type": "object", "properties": {
         "query": {"type": "string"}}, "required": []}},
    {"name": "get_norms",
     "description": "Return the team norms / PM playbook the agent must follow.",
     "input_schema": {"type": "object", "properties": {
         "query": {"type": "string"}}, "required": []}},
    {"name": "propose_stories",
     "description": "Queue a set of backlog stories for human approval (creates nothing; rejected above the item cap).",
     "input_schema": {"type": "object", "properties": {
         "project_id": {"type": "string"},
         "stories": {"type": "array", "items": {"type": "string"}},
         "reason": {"type": "string"}}, "required": ["project_id", "stories"]}},
]


class Bounds:
    """Tracks spend and trips the cost cap. This is enforced OUTSIDE the model."""

    def __init__(self):
        self.cost = 0.0

    def add(self, usage) -> None:
        self.cost += (usage.input_tokens * PRICE_IN
                      + usage.output_tokens * PRICE_OUT) / 1_000_000

    def over_cap(self) -> bool:
        return self.cost >= COST_CAP_USD


OUTPUT_DIR = Path(__file__).parent / "run-output"


def banner(text: str) -> None:
    print(f"\n{'=' * 64}\n{text}\n{'=' * 64}")


# --- Definition of done (M2 loop-spec §2) ----------------------------------
# "The model stopped calling tools" is a definition of quiet, not of done. A run is
# only successful if it actually produced the deliverable, checked structurally here
# rather than asserted by the model.
MIN_DRAFT_CHARS = 200
# A tripwire, not a defence. Any rephrasing defeats a pattern list; the actual
# defence against injection is that no publish, create or merge tool exists, so a
# brief cannot make Cortex act on the world whatever it says. What this catches is
# the one failure the critic already missed: an injection flagged but not escalated.
INJECTION_MARKERS = ("system override", "admin mode", "ignore previous",
                     "ignore all previous", "you are now", "developer mode",
                     "disregard your")
ARTEFACT_PATTERNS = (r"#\d+", r"\b\d{1,3}%")
# The model writes the marker as a markdown heading ("## DONE") as often as the literal
# "DONE:" the prompt asks for. A check stricter than the behaviour it checks produces
# false stucks, which in a real deployment means pulling in a human for nothing.
MARKER = r"(?mi)^[\s>#*_-]*(%s)\b[:*\s]"


def artefacts_in(text: str) -> set[str]:
    """Pull citable artefact tokens (PR/issue ids, metric values) out of text."""
    found: set[str] = set()
    for pattern in ARTEFACT_PATTERNS:
        found.update(re.findall(pattern, text))
    return found


def injection_attempted(brief: str) -> bool:
    """True if the inbound brief carries a known injection marker."""
    lowered = brief.lower()
    return any(marker in lowered for marker in INJECTION_MARKERS)


def activity_was_pulled(source_log: list[str]) -> bool:
    """Did this run actually reach the evidence source?

    "No activity in the window" and "the activity tool was never called" look
    identical to a rule that only counts artefacts, and they are opposites: the
    first is a fact to report, the second means the draft has no evidence behind
    it. get_activity already says which via its `result` field.
    """
    return any(entry.startswith("get_activity(") for entry in source_log)


def check_done(draft: str, source_log: list[str], brief: str = "") -> tuple[str, str]:
    """Classify a proposed output as done / escalate / stuck, with a reason.

    Tokens are drawn from what this run actually pulled, so the check stays honest
    when the fixtures change.
    """
    if not draft.strip():
        return "stuck", "run produced no output at all"
    if re.search(MARKER % "ESCALATE", draft):
        return "escalate", "Cortex escalated to a human"
    if not re.search(MARKER % "DONE", draft):
        return "stuck", "output ended with neither DONE nor ESCALATE"
    if injection_attempted(brief):
        return "stuck", ("the brief carried an injection marker, so this run had to escalate; "
                         "it finished with DONE instead")
    if len(draft.strip()) < MIN_DRAFT_CHARS:
        return "stuck", f"draft is {len(draft.strip())} chars, below the {MIN_DRAFT_CHARS} minimum"
    # Only this project's own activity counts. Pooling every tool result drags in
    # other projects' figures via search_past_updates, and the check then demands the
    # draft cite numbers that belong to someone else's project.
    activity = [entry for entry in source_log if entry.startswith("get_activity(")]
    if not activity_was_pulled(source_log):
        return "stuck", ("the run never pulled activity, so nothing in the draft has evidence "
                         "behind it; a missing evidence source is not a quiet week")
    pulled = artefacts_in("\n".join(activity))
    cited = pulled & artefacts_in(draft)
    if pulled and not cited:
        return "stuck", ("draft cites none of the artefacts this run pulled "
                         f"({', '.join(sorted(pulled))}), so it describes an update "
                         "rather than containing one")
    if not pulled:
        return "done", "no activity in the window, so there is nothing to cite"
    return "done", f"draft cites {', '.join(sorted(cited))}"


def text_of(content) -> str:
    """Join the text blocks of a Messages API response into one string."""
    return "\n".join(b.text for b in content if b.type == "text")


def emit_deliverable(which: str, draft: str, *, accepted: bool,
                     reason: str, cost: float) -> None:
    """Surface AND persist Cortex's drafted status update so it can't get lost in
    the scroll-back. This is still a DRAFT held for human review, never a post,
    there is no publish tool, and an escalated run is held on purpose.

    Runs on every exit: an accepted pass prints the FINAL update; a bound trip or
    escalation prints the LAST draft it managed to write plus why it was held.
    """
    banner("FINAL STATUS UPDATE (draft, validator-approved, NOT posted)" if accepted
           else "LAST DRAFT (held, NOT posted, escalated to a human)")
    if draft.strip():
        print(draft.rstrip())
    else:
        print("(Cortex stopped before it produced a draft, nothing to show.)")
    if not accepted:
        print(f"\nWhy it was held: {reason}")

    if draft.strip():
        OUTPUT_DIR.mkdir(exist_ok=True)
        out = OUTPUT_DIR / f"status-update-{which}.md"
        state = "accepted by validator" if accepted else "HELD, escalated"
        out.write_text(
            f"<!-- Cortex draft, {state}; NOT posted. Run cost ~ ${cost:.4f}. -->\n"
            f"<!-- {reason} -->\n\n{draft.rstrip()}\n", encoding="utf-8")
        print(f"\nSaved draft -> {out.relative_to(Path(__file__).parent)}  "
              f"(for your review, nothing was posted)")


def run(which: str = "happy") -> None:
    client = anthropic.Anthropic()
    bounds = Bounds()
    task = tools.get_task(which)
    if "error" in task:
        print(task)
        return

    banner(f"CORTEX RUN, fixture: task-{which}  (draft {MODEL}, critic {CRITIC_MODEL}, "
           f"auto-queue cap {MAX_QUEUE_ITEMS} items)")
    print(task["body"])

    messages = [
        {"role": "user", "content": f"PM task brief:\n\n{task['body']}"},
    ]
    source_log: list[str] = [task["body"]]
    revisions = 0
    last_draft = ""

    for step in range(1, MAX_ITERATIONS + 1):
        if bounds.over_cap():
            reason = f"cost cap ${COST_CAP_USD} hit at ${bounds.cost:.4f}"
            banner(f"BOUND TRIPPED, {reason}. Halting and escalating to a human.")
            emit_deliverable(which, last_draft, accepted=False,
                             reason=reason, cost=bounds.cost)
            return

        resp = client.messages.create(
            model=MODEL, max_tokens=MAX_OUTPUT_TOKENS, system=CORTEX_SYSTEM,
            messages=messages, tools=TOOL_SCHEMAS)
        bounds.add(resp.usage)

        tool_uses = [b for b in resp.content if b.type == "tool_use"]
        if tool_uses:
            messages.append({"role": "assistant", "content": resp.content})
            results = []
            for call in tool_uses:
                fn = call.name
                args = dict(call.input)
                result = tools.TOOLS[fn](**args)
                source_log.append(f"{fn}({args}) -> {json.dumps(result)}")
                print(f"\n[step {step}] TOOL {fn}({args})")
                print(f"          -> {json.dumps(result)[:300]}")
                results.append({"type": "tool_result", "tool_use_id": call.id,
                                "content": json.dumps(result)})
            messages.append({"role": "user", "content": results})
            continue

        # No tool calls => Cortex produced a proposed output. Check it is the
        # deliverable before paying for a critic call on it.
        proposed = text_of(resp.content)
        last_draft = proposed
        print(f"\n[step {step}] PROPOSED OUTPUT:\n{proposed}")

        verdict_kind, why = check_done(proposed, source_log, task["body"])
        print(f"\n[step {step}] DEFINITION OF DONE: {verdict_kind}, {why}")

        if verdict_kind == "stuck":
            banner(f"STUCK, {why}. Halting and escalating to a human. "
                   f"Run cost \u2248 ${bounds.cost:.4f}")
            emit_deliverable(which, last_draft, accepted=False,
                             reason=f"definition of done not met: {why}",
                             cost=bounds.cost)
            return

        if verdict_kind == "escalate":
            banner(f"ESCALATED by Cortex, handed to a human. Nothing posted. "
                   f"Run cost \u2248 ${bounds.cost:.4f}")
            emit_deliverable(which, last_draft, accepted=False,
                             reason=why, cost=bounds.cost)
            return

        banner("CRITIC, independent validation")
        verdict = review(client, CRITIC_MODEL, proposed, "\n".join(source_log[1:]),
                         task_brief=task["body"])
        # Estimate critic spend too.
        bounds.cost += (verdict["_usage"]["prompt"] * CRITIC_PRICE_IN
                        + verdict["_usage"]["completion"] * CRITIC_PRICE_OUT) / 1_000_000
        print(json.dumps({k: v for k, v in verdict.items() if k != "_usage"}, indent=2))

        if verdict["verdict"] == "pass":
            banner(f"HITL CHECKPOINT, status update + any proposed stories queued for "
                   f"your review. Nothing posted, no commitments made. "
                   f"Run cost ≈ ${bounds.cost:.4f}")
            emit_deliverable(which, proposed, accepted=True,
                             reason="validator passed", cost=bounds.cost)
            return

        if revisions >= MAX_REVISIONS:
            reason = f"validator rejected {MAX_REVISIONS}x (revision cap)"
            banner(f"REVISION CAP hit ({MAX_REVISIONS}). Escalating to a human "
                   f"instead of looping. Run cost ≈ ${bounds.cost:.4f}")
            emit_deliverable(which, last_draft, accepted=False,
                             reason=reason, cost=bounds.cost)
            return

        revisions += 1
        print(f"\n-> critic rejected; revision {revisions}/{MAX_REVISIONS}")
        messages.append({"role": "assistant", "content": resp.content})
        messages.append({"role": "user", "content":
                         "A validator rejected that for these reasons: "
                         f"{verdict['reasons']}. Fix it or escalate."})

    banner(f"MAX ITERATIONS ({MAX_ITERATIONS}) reached without finishing. "
           f"Escalating. Run cost ≈ ${bounds.cost:.4f}")
    emit_deliverable(which, last_draft, accepted=False,
                     reason=f"max iterations ({MAX_ITERATIONS}) reached",
                     cost=bounds.cost)


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "happy")
