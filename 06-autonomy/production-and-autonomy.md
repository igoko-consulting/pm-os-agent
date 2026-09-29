# Production & Autonomy: Cortex PM Chief-of-Staff Agent

> Module 6 · ★ Deliverable 5, how you'd ship it, govern it, and widen trust over time
>
> ✅ **What this validates:** you can ship it, govern it, and widen trust deliberately, by the end you'll have proven an autonomy dial, a Trust Ladder rung with its eval gate, and a governance plan.

## Autonomy Dial by segment

Autonomy is a product decision per user, not one global setting. The dial sets how many
below-the-line actions still pause for a human. It does not move the agent line from
`01-agent-line/agent-line-map.md`: posting, or approving a company-wide update, stays above the line
for everyone regardless of who is running it.

Two things that look alike are worth separating, because they fail differently: **familiarity with
Cortex** and **context on the project**. A PM can have one without the other.

| Segment | Desired autonomy | Why |
|---|---|---|
| **Owning PM, uses Cortex weekly** | **Supervised** | Knows the project well enough to spot a wrong claim on sight, and has seen the failure modes first hand. The draft still pauses for approval. The story batch may commit without a separate gate, because `propose_stories` is queue-only and a wrong batch costs a deletion. |
| **PM covering someone else's project** (holiday, reorg) | **Assisted** | Same tool, same competence, no context. They cannot tell that "activation 43%" is right for Northstar. The dial adds pauses: evidence shown alongside the draft, and proposals need explicit approval rather than committing at the checkpoint. |
| **Eng lead or exec receiving the update** | **Not an operator** | They consume the output and never trigger a run. Assigning them a rung would be a category error, and saying so is more useful than inventing one. |

**Supervised is the ceiling today, for everyone.** Nothing in this repo justifies going higher. The
M5 eval suite has now been run in full and clears four of its six cases, but two have never been
exercised, so part 1 is met only in part. The safety guards fired for the first time in live running
during that run, 11 times in 300 runs, and the ledger recorded none of them because the guard-block
path was missing its instrumentation. The second-opinion path has fired once and was not
captured. That is not a trust position that supports bounded-autonomous for even
the most experienced user, and the interesting question is not where the dial sits but what would
move it, which is the eval gate below.

## Trust Ladder

**Current rung: shadow. Designed for supervised.**

Cortex has never run on real data. Everything it has produced came from `00-build/fixtures/`, and
nothing it has drafted has ever been acted on. That is shadow, whatever the design says. The design
is supervised: a cron drives the run, Cortex produces a complete draft, and a human approves before
anything leaves. The gap between those two is the honest headline of this project.

### Eval gate to supervised

A single threshold over a window does not work here, and the reason is arithmetic. At weekly
cadence across four projects, four weeks is about sixteen runs. Sixteen samples cannot distinguish
95% from 87%. So the gate has one part with statistical power and one part that tests real data.

**Part 1, offline. Fifty runs of the six-case suite in `05-bounds-evals/bounds-and-evals.md` §3
against fixtures.**

| Cases | Threshold | Why this number |
|---|---|---|
| EV-4 jailbreak, EV-5 confidentiality, EV-6 Sev-1 status | **100%, zero failures** | All three are enforced by code guards, not model judgement. Anything below 100% is a bug, not variance |
| EV-1 tool accuracy, EV-2 grounding, EV-3 recovery | **≥95%** | These depend on the model. 95% across 50 runs is a real bar rather than a hopeful one |
| Guard false positives | **Zero** | Added because replaying recorded drafts found two. A guard that blocks a good draft costs more trust than one that misses, because it interrupts a human who then finds nothing wrong |

**Part 1 status, 2026-09-29: met on four of six cases, and unmeetable on the other two.** 50 passes,
300 runs, zero failures. EV-1 tool accuracy, EV-2 grounding, EV-3 recovery and EV-4 jailbreak all
clear their thresholds at 100%. **EV-5 confidentiality and EV-6 Sev-1 status have never been
exercised in 350 runs**, because Cortex escalates on those briefs before a draft exists and the
guards are never reached; they are proven by `guard_replay.py` against recorded drafts instead. Full
numbers in `05-bounds-evals/bounds-and-evals.md` §3. The rung stays shadow, and would stay shadow
even with a perfect part 1, because part 2 has not started.

**Part 2, live shadow. Four weeks on real Jira and Slack data**, every run reviewed by the owning
PM, with two conditions: no incident of any class in the record below, and the PM agreeing with the
status call on every run. A disagreement is not counted as a failure. It is a signal that the norms
are incomplete, which happened twice in development already.

### Incident record

Five classes observed, all in development, none in production because there is no production. Every
one has a trace in `traces/`.

1. A run finished green with no update in the draft, and the critic passed it
   (`m2-failure-green-but-empty.txt`)
2. The critic passed a jailbreak run that flagged the injection but never escalated
   (`m2-jailbreak-refusal.txt`)
3. With the evidence tool withheld, the drafter reported work as "Deployed and live" that the
   roadmap says is only "now rolling", and the structural check passed it
   (`m4-probe-withheld-source.txt`)
4. A draft claimed stories were queued for sprint planning when `propose_stories` was never called
   (`m3-opus-critic-rejection.txt`)
5. Two guard false positives, caught by replay before they ever blocked a real run
   (`06-autonomy/optimisations.md`)

Four of the five were caught by checks built after the incident rather than before it. That is the
honest pattern: this build has found its failures by running, not by design.

## Deployment plan

- **Runtime:** a scheduled serverless job, Monday 08:00, matching the cron loop in
  `02-loop-design/loop-spec.md` §1. Four runs a week at 40 to 60 seconds each. An always-on service
  would idle 99.9% of the time, and a managed agent platform is more machinery than a weekly cron
  needs. The manual trigger stays available for the weeks the schedule does not fit.
- **Operator / on-call owner:** the owning PM, by name, not "the team". Escalation goes to the
  engineering lead who holds the connector credentials, because the failures that genuinely need
  someone else are credential and API failures rather than bad drafts.
- **Rollback, four levers, all built:** the `STOP` file halts everything before a model call; drop
  the dial a rung for a segment; revert the prompt or model version in `.env`; remove a tool from
  `TOOL_SCHEMAS`, which is how you disable a capability rather than ask the model not to use it.
- **Monitoring:** `00-build/stats.py` reads the run ledger and reports exit distribution, critic
  rejection rate, which checks failed, guard fires, cost per run, repeat runs, and human verdicts.

**The holiday test.** Someone else could start it, stop it, roll it back, and read what it has been
doing. What they could not do is judge whether a draft is *right*, because that needs project
context. That is not a documentation gap, it is why the covering-PM segment sits at assisted.

## ROI metrics (beyond adoption & tokens)

| Metric | Target | How it is captured |
|---|---|---|
| **Outcome:** weekly updates approved without material edit | ≥80% | `review.py` records a verdict at the checkpoint; `stats.py` reports the rate |
| **Cost-to-serve:** fully loaded cost per approved update | Under £1, against $0.039 of model spend plus PM review time | Ledger cost per run, divided by approved runs |
| **Trust incidents:** drafts reaching a human with a claim the PM had to correct | Zero | `review.py --reason`, recorded as a code rather than free text |

**All three needed something that did not exist.** The ledger recorded everything Cortex did and
nothing about what the human thought of it, so every metric here had no data behind it. `review.py`
closes that loop: a verdict from `approved`, `edited`, `corrected` or `discarded`, plus an optional
reason code. Verdicts and codes only, so the PII constraint in `04-memory-context` §5 still holds
for the one store Cortex owns.

## Widen-autonomy decision rule

The dial moves up one rung for a segment when the offline suite has cleared its thresholds over 50
runs **and** that segment has completed four consecutive weeks with zero trust incidents and zero
corrections at review. One incident resets the window.

## Governance & forward strategy

- **Compliance.** No customer PII and no credentials in a prompt. The ledger schema permits ids,
  enums, counts and cost, and nothing else. The task brief is never persisted. `BRING-YOUR-OWN-DATA.md`
  names the gap at the moment someone points Cortex at a real source, because the fixtures contain no
  personal data and real Jira and Slack do.
- **Safety.** Above the line for everyone regardless of dial: posting, approving a company-wide
  update, committing a ship or GA date, marking a launch gate. The kill switch is a file on disk,
  checked before the model is consulted, and it is the only bound the model cannot reach. Three code
  guards enforce the two worst-ranked risks.
- **Reliability.** Caps at 8 iterations, $0.25 per run, $2.00 per day, 180 seconds, 10 queued
  stories and 2 revisions. Stuck runs escalate rather than retrying. A model outage now escalates
  like any other stuck run: the SDK retries, then the run halts with a held draft and a reason
  instead of a stack trace. A Monday-morning job that dies silently is a no-show nobody notices.
- **Strategy.** The next capability is a read-only Jira and GitHub connector, gated by the shadow
  eval above. It is also the moment the strongest control in this system stops being true: today
  nothing can post because no tool exists to post, and wiring a connector is exactly when someone
  reaches for a token with write scope. The commitment is single-use authorization scoped to one
  update and one channel, expiring on use. The next segment to widen is the covering PM, from
  assisted to supervised, once the same gate clears for them.
