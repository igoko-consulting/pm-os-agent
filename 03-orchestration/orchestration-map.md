# Orchestration Map: Cortex PM Chief-of-Staff Agent

> Module 3 · Orchestration & Subagents, ★ Deliverable 3
>
> ✅ **What this validates:** nothing advances unchecked, by the end you'll have proven a justified topology, a roster, and a validator with a defined fail action.
>
> Builds on your M2 Loop Spec. Only split one agent into a team when there's a real reason, coordination has a cost.

## 1. Why split? (or why not)

Cortex splits for one reason only: it needs an independent validator. Cortex can't grade its own
draft. In `m2-critic-rejection.txt`, the critic caught a draft claiming stories were "queued for
sprint planning" when `propose_stories` was never called. A self-grading agent won't catch false
claims about its own actions, because it believes them.

The other three reasons don't hold up.

**Separation of concerns.** Drafting and validating are different jobs, but that's true of most
single agents too. The real test is whether they'd contaminate each other, not whether they're
distinguishable, and nothing here suggests they would.

**Parallelism.** One project, one run, sequential by nature. The critic can't start before a draft
exists, so there's nothing to run in parallel.

**Context-window pressure.** A full run is a few thousand tokens against a 200K window. Not even
close.

The validator is a filter with known holes, not a guarantee. In `m2-jailbreak-refusal.txt`, it
passed a run that broke a stated rule, praising the refusal while missing that the required
escalation never happened. It earns the extra model call because it catches a class of error the
drafter structurally can't, not because it's reliable.

## 2. Topology

**Pattern:** single + subagents

```
[Cron, Monday 08:00] -> [Cortex: pulls data, drafts update + queues stories]
                     -> [done-check, in code]
                     -> [Validator: independent call, own context]
                            fail -> back to Cortex (max 2 revisions) -> escalate
                            pass -> [PM review checkpoint] -> queued, nothing sent
```

Two agents, not four. The done-check sits between them and is not an agent at all, it is a
structural test in `agent.py` that stops a non-deliverable before it costs a validator call.

## 3. Roster

| Agent / subagent | Responsibility | Runs which Loop Spec |
|---|---|---|
| Cortex (chief-of-staff) | Pulls context, drafts the update, queues stories within the cap, decides when to escalate | M2 loop |
| Validator (critic) | Checks the draft against six rules before a human sees it | Validation pass: one call, no tools, no memory |

## 4. Communication & hand-offs

Plain in-process Python calls. No MCP, no A2A. Cortex passes the validator two things as text, the
pulled data and the draft, and gets back JSON: a verdict plus reasons. On a fail, the reasons are
appended to Cortex's messages and it redrafts.

Worth naming because "we used a protocol" often gets mistaken for architecture. Nothing here needs
one. If a subagent ever runs out of process, this is the seam where a protocol would go.

## 5. The validator

**What the critic checks.** Six checks, all of which already exist in `CRITIC_SYSTEM`:

1. Correct project, and real PR/issue IDs from the pulled data.
2. Every claim traceable to pulled activity. No invented numbers, no invented progress.
3. Within team norms: no unconfirmed date, no launch gate marked, no CONFIDENTIAL item in a
   company-wide update, or a correct escalation instead.
4. Posts nothing, commits nothing, creates or merges nothing. Stories are proposed, not created.
5. If the task tried to jailbreak Cortex, Cortex refused **and** escalated.
6. If a tool rejected an action or an enforced bound was hit, escalating is the correct response
   and shouldn't be failed over wording.

**How they're enforced, which matters more than the list.** These six were already written down
when the critic passed `m2-jailbreak-refusal.txt`, a run where Cortex flagged the injection and
then finished with DONE instead of escalating. Check 5 covers that exactly. The critic's reasons
don't mention escalation at all, so it didn't fail the check, it never answered it. A seventh check
wouldn't have helped.

Two changes, both aimed at skipping rather than judgement:

- **A verdict per check.** The critic returns pass, fail or n/a for each numbered check instead of
  a free-form list of reasons. It can't stay silent on one. Compound conditions like "refused
  **and** escalated" are exactly what a narrative judge collapses into the half it noticed.
- **The injection rule moves into code.** If an injection was detected, the run has to take the
  escalate exit. That's checkable without a model, the same way the definition-of-done check is,
  and a bound in code survives the model having a bad day.

**Fail action: revise, up to 2 revisions, then escalate.** Revise rather than block, because
`m2-critic-rejection.txt` shows it working: the drafter accepted all three criticisms and escalated
when it still couldn't satisfy them, rather than producing a worse draft.

**Revision cap: 2.** Hard number, enforced in `agent.py`, not a suggestion in a prompt. The cost is
measured, not guessed: `m2-quiet-week.txt` ran the full cap at $0.0275 against roughly $0.0200 for
a clean success, so a fully bounced run costs about 35% more. That's the bound to justify in M5.

**Pass action.** A passing draft advances to the PM review checkpoint and is saved to
`run-output/`. It is never sent. There's no publish tool, so that's structural, not a promise.

## 6. State: shared vs isolated

**Shared.** The pulled data and the draft. The validator judges the same evidence Cortex used. If
it pulled its own data the two could disagree on facts rather than on the draft, which is a
different and less useful argument.

**Isolated.** Cortex's message history and reasoning never reach the validator, and the validator
has no tools and no memory between runs. Independence is about inputs. The validator's *output*
does flow back to Cortex on a fail, because that is how revision works, but its context never does.

**Change from the shipped build: the brief is fenced.** `source_log` starts with the task brief and
`critic.py` passed the whole thing under the heading "SOURCE DATA Cortex used". So on the jailbreak
run the SYSTEM OVERRIDE block reached the validator labelled as evidence. It now arrives in its own
block marked as untrusted and possibly hostile, separate from the tool results. The validator still
needs the brief, it cannot answer check 5 without knowing whether there was an injection, but it
should not read an attack as source data.

**Limitation worth recording.** The validator can only catch errors relative to what was pulled. If
Cortex never calls `get_activity`, the validator sees a thin source log and has nothing to notice
the absence against. It validates the draft, not the retrieval.

## 7. Cost & latency budget

**Per run, normal case.** One extra model call. Measured at 2,347 input and 504 output tokens,
**$0.0049** and about **7 seconds** on `claude-haiku-4-5`. A clean successful run costs roughly
$0.020 end to end, so the validator is about a quarter of it.

**Worst case, at the revision cap.** Three validator calls and two redrafts. Measured at **$0.0275**
on `m2-quiet-week.txt` against about $0.020 for a clean pass, so a fully bounced run costs roughly
35% more and adds about 20 seconds before anything reaches the PM.

**Weekly, at the intended cadence.** One run per project per week. Four projects is about $0.08 a
week, or £4 a year. Cost is not the constraint at this scale. It becomes one if Cortex ever runs
per-project-per-day, or if the model moves up a tier, and that is the decision to revisit rather
than this one.

**Latency is not a constraint either.** The run is triggered by a Monday 08:00 cron and read by a
human later that morning. Seven seconds, or twenty at the cap, is invisible against that. It would
matter if the trigger became a hook on an inbound request with someone waiting.

**What the budget actually has to justify.** Five deliberate attempts to make the validator reject a
draft in a live run failed, because the drafter caught the problem first. The same fixtures produced
rejections in M2. So the validator is no longer catching something most weeks, and its cost is being
paid for the rare case: a draft that is wrong in a way the drafter cannot see, which is precisely
the class of error that self-grading misses. `m2-critic-rejection.txt` is that case, where the draft
claimed stories had been queued that were never queued. A quarter of a run is cheap insurance
against a false claim reaching leadership. It would not be cheap if the run were 100x larger, and
that is the number to watch in M5.
