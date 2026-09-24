"""Cortex mock tools, the tools your PM chief-of-staff agent is allowed to call.

These are plain Python functions over the files in `fixtures/`. They are imported
directly by `agent.py`, so this file is the single place that defines what Cortex
can and cannot do. Ask your coding agent to add, remove, or tighten a tool here.

Design note that matters for the course: there is deliberately NO publish tool.
Cortex can read and DRAFT a status update, and it can PROPOSE backlog stories (which
are capped and queued for a human), but it can never post to a channel, create or
merge a ticket/PR, commit a ship date, or mark a launch gate. The agent line is
enforced here, in infrastructure, not by a prompt.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"

# Commitment bound (M5). A run that tries to queue more than this many backlog
# stories is rejected by infrastructure and must be escalated, even if the PRD
# would justify more. Auto-committing a flood of "real" work is the money analog.
MAX_QUEUE_ITEMS = int(os.environ.get("CORTEX_MAX_QUEUE_ITEMS", "10"))


# Fallback only. The reporting window lives on each project record in
# projects.json, so the data owns the fact rather than the code. It was a constant
# here until the 2026-07-06 data pack moved the activity into July and left the
# window in June: get_activity then reported a window that did not contain its own
# data, and the draft repeated it under a leadership heading. A fact kept next to
# the data it has to agree with cannot drift away from it.
ACTIVITY_WINDOW = "unknown"


def _load_json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def get_task(which: str = "happy") -> dict:
    """Read the inbound PM task brief to work on.

    Args:
        which: one of "happy", "missing-data", "jailbreak", "at-risk", "embargoed", "bad-numbers", "quiet-week", "rounding", "probe".
    Returns the raw task text plus its source label.
    """
    path = FIXTURES / f"task-{which}.md"
    if not path.exists():
        return {"error": f"no task fixture named '{which}'",
                "available": ["happy", "missing-data", "jailbreak", "at-risk", "embargoed", "bad-numbers", "quiet-week", "rounding", "probe"]}
    return {"which": which, "body": path.read_text()}


def get_project(project_id: str) -> dict:
    """Look up a single project by its ID. Returns {"error": ...} if not found."""
    project_id = str(project_id).strip()
    projects = _load_json("projects.json")
    record = projects.get(project_id)
    if record is None:
        return {"error": "project_not_found", "project_id": project_id,
                "hint": "no such project in the system",
                "known_projects": list(projects.keys())}
    # Return the project WITHOUT its activity blob; activity is a separate tool call
    # so the agent has to deliberately pull it (a teachable retrieval step).
    return {k: v for k, v in record.items() if k != "activity"}


def get_activity(project_id: str) -> dict:
    """Pull recent engineering activity (merged PRs, open issues, Sev-1s) for a project.

    `result` distinguishes a genuinely quiet week from a feed that returned nothing.
    Without it both look like an empty list, and the agent has to escalate on the
    ambiguity rather than report the quiet week it is actually looking at.
    """
    project_id = str(project_id).strip()
    projects = _load_json("projects.json")
    record = projects.get(project_id)
    if record is None:
        return {"error": "project_not_found", "project_id": project_id}
    activity = record.get("activity", [])
    return {"project_id": project_id,
            "window": record.get("window", ACTIVITY_WINDOW),
            "result": "activity_found" if activity else "no_activity_in_window",
            "activity": activity}


def search_past_updates(query: str = "") -> dict:
    """Search previous status updates and decisions for tone and precedent (the
    memory/retrieval surface).

    Naive keyword overlap over a small fixture so M4's retrieve-vs-reason lesson is
    concrete: relevant precedent is returned, irrelevant precedent is not."""
    query = (query or "").lower()
    corpus = _load_json("past-updates.json") + _load_json("decision-log.json")
    terms = {t for t in query.replace("#", " ").split() if len(t) > 2}
    hits = []
    for u in corpus:
        haystack = f"{u.get('project','')} {u.get('summary','')} {u.get('theme','')}".lower()
        if terms and any(term in haystack for term in terms):
            hits.append(u)
    # No agentic move can grade the output of a tool that lies about its own
    # results. This used to return `hits or corpus[:2]`, so a query that matched
    # nothing came back with the first two items in the corpus labelled "matches".
    # On the missing-data run, a query about P-HALO returned Northstar's figures
    # under that key. Honest empty beats confident wrong.
    return {"query": query,
            "result": "matches_found" if hits else "no_matches",
            "matches": hits,
            "note": "prior updates + decisions for precedent, team norms still govern."}


def get_roadmap(query: str = "") -> dict:
    """Return the roadmap. Some items are flagged confidential/embargoed, those must
    never appear in an external or company-wide update. `query` is a hint; the file
    is small enough to return whole so the agent can cite what it relied on."""
    text = (FIXTURES / "roadmap.md").read_text()
    return {"query": query, "roadmap": text,
            "warning": "items marked CONFIDENTIAL must not be shared outside the core team."}


def get_backlog(project_id: str) -> dict:
    """List a project's backlog items, open and in-progress, with what is already done.

    Added because the brief asks Cortex to propose stories "from PRD-Northstar-v3"
    and no tool listed a backlog. It filled the gap from PRD prose, which is how two
    stories for work merged in the same run ended up proposed
    (06-autonomy/traces/m4-happy-redundant-stories.txt). Done items are returned as
    ids only: visible enough not to be re-proposed, not so present that they land in
    the proposal set.
    """
    project_id = str(project_id).strip()
    if project_id not in _load_json("projects.json"):
        return {"error": "project_not_found", "project_id": project_id}
    items = _load_json("backlog.json").get(project_id, [])
    done = [i for i in items if i.get("status") == "done"]
    live = [i for i in items if i.get("status") != "done"]
    return {"project_id": project_id,
            "result": "backlog_found" if items else "no_backlog_items",
            "open": live,
            "done_count": len(done),
            "done_ids": [i["id"] for i in done],
            "note": "propose only from `open`; `done_ids` are already delivered, do not re-propose them."}


def get_norms(query: str = "") -> dict:
    """Return the team norms / PM playbook. `query` is a hint; the full playbook is
    small enough to return whole so the agent can cite the exact rule it relied on."""
    text = (FIXTURES / "team-norms.md").read_text()
    return {"query": query, "norms": text}


def propose_stories(project_id: str, stories=None, reason: str = "") -> dict:
    """PROPOSE a set of backlog stories for a human to approve. This creates NOTHING
    in the tracker, it queues a request. A batch larger than CORTEX_MAX_QUEUE_ITEMS
    is rejected by infrastructure and must be escalated. This is the commitment bound,
    enforced outside the model (M5)."""
    if isinstance(stories, str):
        stories = [stories]
    if not isinstance(stories, list):
        return {"error": "invalid_stories", "stories": stories}
    if len(stories) > MAX_QUEUE_ITEMS:
        return {"status": "rejected",
                "error": "batch_exceeds_queue_cap",
                "count": len(stories),
                "cap_items": MAX_QUEUE_ITEMS,
                "action": "escalate to a human, do not split the batch to dodge the cap"}
    return {"status": "queued_for_approval",
            "project_id": str(project_id).strip(),
            "count": len(stories),
            "stories": stories,
            "reason": reason,
            "note": "queued for a human to approve, nothing was created in the tracker."}


# Registry the agent loop reads. Add a tool here and the agent can call it.
# Note what is ABSENT: there is no post_update, no create_issue, no merge_pr,
# no commit_ship_date, no close_bug, no tool that acts on the world.
TOOLS = {
    "get_task": get_task,
    "get_project": get_project,
    "get_activity": get_activity,
    "search_past_updates": search_past_updates,
    "get_roadmap": get_roadmap,
    "get_backlog": get_backlog,
    "get_norms": get_norms,
    "propose_stories": propose_stories,
}
