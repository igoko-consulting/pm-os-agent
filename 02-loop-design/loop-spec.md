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

Done is therefore checked structurally in the loop, not asserted by the model. The draft must carry
a DONE or ESCALATE marker, be non-trivial in length, and cite at least one real artefact from this
project's own activity pull. A bound enforced in code survives the model having a bad day, which is
the same argument that keeps `propose_stories` queue-only.

Two scoping rules matter, and both were found by the check getting them wrong first. Artefacts come
only from the `get_activity` result for the project in hand, never from every tool result: pooling
them let another project's figures arrive through `search_past_updates`, and a correct update was
marked stuck for not citing numbers that belonged elsewhere. And when the activity pull is empty,
the artefact rule disables itself, because a quiet week has nothing to cite and requiring a citation
would make an honest update impossible. The marker and length checks still apply.

The general lesson is worth more than either rule: a check stricter than the behaviour it checks
produces false stucks, and a false stuck costs more trust than a miss. It interrupts a human who
then finds nothing wrong.

## 3. Stop conditions

| Condition | What it looks like | What happens |
|---|---|---|
| **Success** | Draft contains a status update citing at least one pulled artefact, and the critic passed it | Queue at the HITL checkpoint, save to `run-output/`, stop. Nothing sent. |
| **Stuck / give up** | Project or activity data cannot be pulled; or the critic rejects twice (revision cap); or the turn cap or cost cap trips; or the run ends with no status update in the draft; or the brief carried an injection marker and the run did not take the escalate exit (added M3) | Halt, log why, escalate with what it tried. Hold the last draft rather than discarding it. |
| **Escalate to human** | Story batch exceeds the queue cap; an unconfirmed GA date or launch-gate call is required; a CONFIDENTIAL or embargoed roadmap item would have to appear; an open Sev-1 is in play; the brief contains an instruction trying to change Cortex's rules | Stop and hand to the human who owns that call. Do not work around it, and do not split a batch to get under the cap. |

**What status colour does a quiet week carry? Settled in practice, never decided.** The norms say a
quiet week is reportable and must not imply progress that did not happen. They still do not say how
to grade it. When this was written the critic rejected any colour as unevidenced and a quiet week
ran the full revision cycle and escalated. After the M3 changes it passes: Cortex reports the
project's own recorded status from `get_project` (`on_track`, shown green) rather than deriving a
colour from a week with no activity, and the validator accepts that because it traces to pulled
data. See `06-autonomy/traces/m3-quiet-week-passes.txt`.

That is a reasonable answer and it is not mine. An unwritten reporting rule was settled by the
drafter and ratified by the validator, with no human in the loop, and the only reason it is visible
at all is that the earlier behaviour was written down here to compare against. It is worth deciding
deliberately rather than inheriting: carrying the last known status forward is defensible weekly and
becomes misleading if a project sits quiet for a month while its recorded status goes stale.

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
| **Subagents** (independent check when the loop can't grade itself) | The critic runs as an independent check, on a stronger model than the drafter. M3 settled the topology as single + subagents and kept it at one validator: see `03-orchestration/orchestration-map.md`. |
| **State tracking** | Durable context plus a per-project run ledger, per §4. |

> Context plan (M4) and the hand-off to bounds & evals (M5) come in later modules, you'll add them to their own deliverables then, not here.

## Link to live loop

_[path to your agent in `00-build/`]_
