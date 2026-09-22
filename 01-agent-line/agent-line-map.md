# Agent Line Map: Cortex PM Chief-of-Staff Agent

> Module 1 · The Agent Line
>
> ✅ **What this validates:** every risky action has a clear owner, by the end you'll have proven an above/below-the-line map with HITL checkpoints, scored on reversibility, blast radius, and measurability.

## The workflow, decision by decision

List every discrete decision or action in your agent's workflow, then score each one and place it **above** the line (a human owns it) or **below** (the agent owns it). Borderline calls get an HITL checkpoint.

| Decision / action | Reversibility (H/M/L) | Blast radius (H/M/L) | Measurability (H/M/L) | Above / Below | HITL? |
|---|---|---|---|---|---|
| Pull project state + recent GitHub/Jira activity | H | M | M | Below | none |
| Decide relevant context (what belongs in this week's update) | H | H | L | Below | draft review (shared gate) |
| Draft the weekly leadership status update | H | H | M | Below | draft review (shared gate) |
| Decide tone / commitment level (green/yellow/red, whether to state a date) | H | H | M | Below | draft review (shared gate) |
| Flag at-risk / escalation (spotting something needs raising) | H | H | M | Below | draft review (shared gate) |
| Choose what to escalate (which items actually go to a human) | H | H | M | Above | required |
| Propose next sprint's stories from the PRD (within cap) | H | L | L | Below | draft review (shared gate) |
| Post the update to a channel / approve a company-wide one | L | H | H | Above | required |

Items 2 to 5 and item 7 share a single HITL checkpoint: the moment a human reads the draft.
Gating each separately would put six approvals in one weekly run, which is a copilot, not an agent.
Item 7 was initially left ungated on the grounds that `propose_stories` only queues and creates
nothing. It is folded into the same gate instead, because the proposed stories already surface
inside the draft a human reads. Adding them to that review costs nothing, adds no step, and closes
the only ungated row with low measurability.

## Agent anatomy (sketch)

- **Model:** `claude-haiku-4-5` for drafting and tool use. Cheap, fast, and sufficient on this
  workload. Escalate to `claude-opus-5` for the critic only: it is the last check before a human
  sees anything, and it runs once per loop. Wired in M3: `CORTEX_CRITIC_MODEL` in `.env`, passed
  separately from the drafting model in `agent.py`, and priced separately in the cost estimate.
  The cost delta is not small, it is about 10x per call, and it earned it on the first live run by
  catching a fabricated forward target the cheaper critic had been passing. See
  `03-orchestration/orchestration-map.md` Field 7.
  (Worth separating: `claude-opus-5` is also the coding agent building Cortex. That is a different
  bill from Cortex's own runtime model.)
- **Tools:** read-only project lookup, activity pull, past-update search, roadmap, and team norms,
  plus `propose_stories`, which queues a batch and creates nothing. Deliberately absent: post,
  create, merge, close, commit-date. The limit is enforced by what exists in `tools.py`, not by a
  prompt.
- **Memory:** durable context persists (team norms, roadmap, decision log). Per-run work is
  disposable (drafts, traces, tool results). Nothing about a run survives it.
- **Loop:** placeholder, defined in M2 loop-spec.md
- **Bounds:** placeholder, defined in M5 bounds-and-evals.md
- **Evals:** placeholder, defined in M5 bounds-and-evals.md

## The golden rule, applied

The rule I used throughout: where the pre-work is done, Cortex proposes below the line. The actual
decision, or the point where something reaches a person, sits above.

1. **Pull project state and activity** sits below the line. Easy to reverse, medium blast radius,
   medium to verify. Deciding factor: reversibility. A bad pull produces a bad draft, and drafts
   are disposable.
2. **Decide relevant context** sits below the line with a gate. Easy to reverse, high blast radius,
   hard to verify. Deciding factor: measurability. What gets left out is invisible afterwards, so a
   human has to see what went in.
3. **Draft the update** sits below the line with a gate. Easy to reverse, high blast radius, medium
   to verify. Deciding factor: blast radius. A false claim reaching leadership is the damage, and
   the gate is what stops it.
4. **Decide tone and commitment level** sits below the line with a gate. Easy to reverse, high
   blast radius, medium to verify. Deciding factor: blast radius. Calling a red project green
   misleads the people funding it.
5. **Flag at-risk and escalation** sits below the line with a gate. Easy to reverse, high blast
   radius, medium to verify. Deciding factor: blast radius. A missed risk compounds quietly until
   it lands.
6. **Choose what to escalate** sits above the line. Easy to reverse, high blast radius, medium to
   verify. Deciding factor: blast radius. A wrong call here removes the human checkpoint rather
   than being caught by it, which is what separates it from items 3 to 5 despite identical scores.
7. **Propose a capped story batch** sits below the line with a gate. Easy to reverse, low blast
   radius, hard to verify. Deciding factor: measurability. Blast radius alone would leave it
   ungated, since `propose_stories` creates nothing and a wrong batch costs a deletion. But there
   is no way to tell afterwards whether the right stories were proposed, and the batch already
   surfaces inside the draft a human reads, so it joins the same gate at no extra cost.
8. **Post the update or approve a company-wide one** sits above the line. Hard to reverse, high
   blast radius, easy to verify. Deciding factor: reversibility. Nobody can un-read a false status
   or a leaked embargoed item.

## Hardest call

Items 2 and 3. I first put "decide relevant context" above the line and "draft the update" below,
which does not hold. Drafting is relevance selection, so a human owning relevance would mean
stopping the run mid-way and handing over raw material before anything is written. I resolved it by
putting selection below the line and review above: Cortex decides and drafts, the human sees both
at one checkpoint.

The axis that settled it was **measurability**. What Cortex leaves out is invisible after the fact,
so the control has to be a human seeing what went in, not a human choosing it up front.
