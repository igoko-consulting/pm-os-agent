# Loop Spec: Cortex PM Chief-of-Staff Agent

> Module 2 · Loop Engineering, ★ Deliverable 2
>
> ✅ **What this validates:** the agent knows when to run and when to stop, by the end you'll have proven a one-page Loop Spec with a trigger, a definition of "done," and explicit stop conditions.
>
> Your one-page blueprint for how the work you handed to the agent (M1) actually *runs*.
> An agent is just a prompt that fires itself, this spec says when it fires, what "done" means, and what it needs to do the job. Living document; refine as the course progresses.

## 1. Trigger & loop type

**Chosen type:** cron, with a manual trigger as backup.

Monday 08:00, one run per project I own, ahead of the leadership sync, so the draft is waiting when
I sit down. The weekly update is calendar-driven: it is due on a schedule whether or not anything
happened that week. The manual trigger covers the weeks the schedule does not fit.

**Ruled out.**

- **Hook:** nothing reliable to react to, and a quiet week still needs an update saying so.
- **Heartbeat:** nothing changes between Mondays that anyone needs to act on, so continuous polling
  would spend money to find out nothing moved.
- **Goal:** the deliverable is fixed and weekly, not open-ended, and a goal loop would have Cortex
  deciding for itself when it was done, which is what the critic exists to prevent.

**Dedupe.** One run per project per ISO week. If the trigger fires twice, the second run replaces
the existing draft rather than creating a second one. The build already overwrites by filename in
`run-output/`, so this is close to current behaviour.

## 2. Goal / definition of done

One run produces a complete status update for one project, grounded in that week's pulled activity,
plus any proposed stories, sitting in `run-output/` for a human to approve. Cortex never sends.

A run that ends without a status update in the draft is not done, it is stuck. This is not
hypothetical: a run on 2026-09-17 finished green, the critic passed it, and the saved draft
contained only a story-proposal summary and a self-reported data-lineage note describing an update
that was never written. "The model stopped calling tools" is a definition of quiet, not a
definition of done.

Done is therefore checked structurally in the loop, not asserted by the model: the draft must be
non-trivial in length and must cite at least one real artefact from the pulled data (a PR id, an
issue id, or the activation metric). A bound enforced in code survives the model having a bad day,
which is the same argument that keeps `propose_stories` queue-only.

## 3. Stop conditions

| Condition | What it looks like | What happens |
|---|---|---|
| **Success** | Draft contains a status update citing at least one pulled artefact, and the critic passed it | Queue at the HITL checkpoint, save to `run-output/`, stop. Nothing sent. |
| **Stuck / give up** | Project or activity data cannot be pulled; or the critic rejects twice (revision cap); or the turn cap or cost cap trips; or the run ends with no status update in the draft | Halt, log why, escalate with what it tried. Hold the last draft rather than discarding it. |
| **Escalate to human** | Story batch exceeds the queue cap; an unconfirmed GA date or launch-gate call is required; a CONFIDENTIAL or embargoed roadmap item would have to appear; an open Sev-1 is in play; the brief contains an instruction trying to change Cortex's rules | Stop and hand to the human who owns that call. Do not work around it, and do not split a batch to get under the cap. |

Escalation routes to the HITL checkpoints set in `01-agent-line/agent-line-map.md`: the shared draft
review gate for anything Cortex prepared, and the human owner for the two above-the-line decisions
(what gets escalated, and whether anything is posted).

## 4. State

**Durable context persists.** Team norms, the roadmap, and the decision log are read sources that
carry across runs.

**A run ledger persists.** Project, ISO week, and outcome, one row per run. This is what the dedupe
rule in §1 needs: without it, "one run per project per ISO week" only works by accident, because
the draft filename happens to collide. Today Cortex has no ledger and relies on that accident.

**Per-run work is disposable.** Drafts, traces, and tool results do not survive the run that made
them.

**Scope is per project.** State never crosses projects. P-ORBIT is embargoed, and shared state is
how an embargoed item ends up in a Northstar update.

Past drafts are deliberately not persisted beyond what `search_past_updates` returns. Carrying them
forward would let last week's mistake propagate into this week's update.

## 5. The five things a loop can lean on

| Component | For Cortex |
|---|---|
| **Work tree** (isolated workspace per run, a git worktree) | Not needed yet, because one run writes one markdown draft and never touches a repo or a shared workspace. Revisit if runs go parallel across projects. |
| **Skills** (reusable capabilities) | Not needed yet, because the update format lives in one prompt. Worth extracting if the format hardens or Cortex starts producing other document types. |
| **Plugins / connectors** (tools & access, optional if you don't have one yet) | None wired. Runs on fixtures today. Planned: read access to GitHub and Jira for activity, and somewhere to leave the draft for review. |
| **Subagents** (independent check when the loop can't grade itself) | The critic already runs as an independent check. Topology and whether to split further is M3's call. Placeholder → `03-orchestration/orchestration-map.md`. |
| **State tracking** | Durable context plus a per-project run ledger, per §4. |

> Context plan (M4) and the hand-off to bounds & evals (M5) come in later modules, you'll add them to their own deliverables then, not here.

## Link to live loop

_[path to your agent in `00-build/`]_
