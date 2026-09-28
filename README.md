# Cortex, a PM Chief-of-Staff Agent

> A PM chief-of-staff that drafts the weekly leadership update from real project data, checks its own work against the evidence it pulled, and stops at a human checkpoint because it has no tool that can post.

_Martin Cook · Agentic Loops for PMs · September 2026_

Repo: https://github.com/igoko-consulting/pm-os-agent

This repo is my final project for the Agentic Loops for PMs Certification, **Cortex**. Each module’s artifact lives in its own folder; this README is the dashboard and the pitch.

---

## Module artifacts

### M1 · The Agent Line
- **Agent-line map**: [`01-agent-line/agent-line-map.md`](01-agent-line/agent-line-map.md)

### M2 · Loop Engineering
- **Loop spec**: [`02-loop-design/loop-spec.md`](02-loop-design/loop-spec.md)

### M3 · Orchestration &amp; Subagents
- **Orchestration map**: [`03-orchestration/orchestration-map.md`](03-orchestration/orchestration-map.md)

### M4 · Context Engineering &amp; Memory
- **Memory &amp; context plan**: [`04-memory-context/memory-and-context.md`](04-memory-context/memory-and-context.md)

### M5 · Bounds &amp; Evals
- **Bounds &amp; evals**: [`05-bounds-evals/bounds-and-evals.md`](05-bounds-evals/bounds-and-evals.md)

### M6 · Autonomy &amp; Production
- **Production &amp; autonomy plan**: [`06-autonomy/production-and-autonomy.md`](06-autonomy/production-and-autonomy.md)
- **Prototype write-up**: [`06-autonomy/prototype.md`](06-autonomy/prototype.md)

---

## Ship plan

### Autonomy dial (per segment)
- Owning PM, uses Cortex weekly → Supervised. Knows the project well enough to spot a wrong claim. Draft still pauses; the story batch may commit at the checkpoint.
- PM covering someone else's project → Assisted. Same tool, same competence, no context. Cannot tell that "activation 43%" is right for Northstar, so proposals need explicit approval.
- Eng lead or exec receiving the update → Not an operator. They consume output and never trigger a run. Assigning a rung would be a category error.
- Supervised is the ceiling for everyone today. The dial never moves the agent line: posting and approving a company-wide update stay above it regardless of user.

### Trust Ladder rung + eval gate
Current rung: shadow. Designed for supervised. Cortex has never run on real data and nothing it has drafted has been acted on.

Gate to supervised, two parts, because sixteen runs cannot distinguish 95% from 87%:

Offline, 50 runs of the six-case suite: EV-4 jailbreak, EV-5 confidentiality and EV-6 Sev-1 status at 100% (code-enforced, so anything less is a bug); EV-1 tool accuracy, EV-2 grounding and EV-3 recovery at ≥95%; zero guard false positives.
Live shadow, 4 weeks on real Jira and Slack, every run reviewed, zero trust incidents, and the PM agreeing with the status call each time.

Incident record: five classes observed in development, all traced, none in production because there is no production. Four of the five were caught by checks built after the incident, not before.

### Deployment plan
- Runtime: scheduled serverless job, Monday 08:00, matching the M2 cron loop. Four runs a week at 40 to 60 seconds. Always-on would idle 99.9% of the time.
- On-call: the owning PM by name. Escalation to the eng lead holding connector credentials, because the failures needing someone else are credential and API failures.
- Rollback, four levers, all built: STOP file halts before any model call; drop the dial a rung; revert prompt or model in .env; remove a tool from TOOL_SCHEMAS to disable a capability rather than ask it not to use one.
- Monitoring: stats.py reads the run ledger for exit distribution, critic rejection rate, checks failed, guard fires, cost per run, repeat runs and human verdicts.

### ROI metrics + widen-autonomy rule
- Outcome: ≥80% of weekly updates approved without material edit. Captured by review.py at the checkpoint.
- Cost-to-serve: under £1 per approved update fully loaded, against $0.039 of model spend plus PM review time.
- Trust incidents: zero drafts reaching a human with a claim the PM had to correct, captured as a reason code.
- Widen rule: the dial moves up one rung for a segment when the offline suite has cleared its thresholds over 50 runs and that segment has completed four consecutive weeks with zero trust incidents and zero corrections at review. One incident resets the window.

### Governance &amp; strategy
- Compliance: no customer PII or credentials in a prompt. The ledger permits ids, enums, counts and cost only. The brief is never persisted.
- Safety: above the line for everyone regardless of dial, posting, approving company-wide, committing a date, marking a launch gate. Kill switch is a file on disk checked before the model is consulted, the only bound the model cannot reach. Three code guards enforce the two worst-ranked risks.
- Reliability: 8 iterations, $0.25 per run, $2.00 per day, 180s, 10 queued stories, 2 revisions. A model outage escalates with a held draft instead of a stack trace.
- Strategy: next capability is a read-only Jira and GitHub connector, gated by the shadow eval. That is also when the strongest control stops being true, so the commitment is single-use authorization scoped to one update and one channel, expiring on use, not a standing write token.

---

## Evidence

The claims in the ship plan are backed by recorded runs rather than assertions.

- **[`06-autonomy/traces/`](06-autonomy/traces/)** — 25 indexed runs with what each demonstrates,
  which anatomy item it proves, and which data version it ran against. Includes the failures: a run
  that finished green with no update in it, a validator that passed a jailbreak it should have
  escalated, and the grounding probe where the drafter fabricated once its evidence source was
  withheld.
- **[`06-autonomy/build-insights.md`](06-autonomy/build-insights.md)** — friction, learnings, the
  aha, and what I would do differently.
- **[`06-autonomy/optimisations.md`](06-autonomy/optimisations.md)** — every change made beyond the
  lab, with measured before and after. A routine run went from $0.075 to $0.039 while the expensive
  validator stayed on every run carrying a risk signal.
- **[`00-build/`](00-build/)** — the running agent. `agent.py` (loop, bounds, guards), `critic.py`,
  `prompts.py`, `tools.py`, plus `stats.py`, `review.py` and `guard_replay.py`.

---

## Build insights

- **Friction point.** Documents drifted from the build in every module, and nothing fails when a document is wrong, so the only way to find it is to go looking. A document nobody can trust is not a control.
- **Key learning.** A bound is only real if it is in code. The strongest control in the system is a tool that does not exist: Cortex cannot post because there is no publish function, and no prompt injection changes that.
- **Aha moment.** Writing the plan found more defects than running the build. Every ROI metric had no data behind it, a model outage killed the run silently, and the dedupe rule had no state to dedupe against. None came from a failing run.

---

_Certification submission, Agentic Loops for PMs Certification._
