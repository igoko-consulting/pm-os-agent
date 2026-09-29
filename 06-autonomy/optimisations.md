# Optimisations

Changes made beyond the lab's requirements, each with measured before and after. Kept separate from
the module deliverables because none of these were asked for: they came out of running the thing and
noticing what it cost or what it missed.

Numbers are per run on the happy-path fixture, drafter `claude-haiku-4-5`.

## Cost

| Change | Before | After | Why it is safe |
|---|---|---|---|
| **Critic note cap, 25 words** | $0.075 | $0.0552 | Critic output was ~70% of the critic's cost and ~half a run's. Notes are read by a human scanning a verdict; `reasons` still carries the detail on failures. Nothing about what the checks catch changed. |
| **Risk-routed critic** | $0.0552 | $0.0389 | Routine runs validate on `claude-sonnet-5`; `claude-opus-5` is used when the run carries a risk signal. See the routing table below, and `traces/m5-risk-routed-sonnet.txt`. |
| **Cumulative** | **$0.075** | **$0.0389** | ~48% off a routine run. At four projects weekly, roughly $8 a year against $16. |

### Why routing, and not "cheap first, escalate on fail"

The obvious tiering is to validate cheaply and escalate to the stronger model when the cheap one
fails. That optimises the wrong direction. A false *fail* costs a wasted revision cycle; a false
*pass* puts a fabrication in front of a human. Escalating on fail means the stronger model only ever
sees drafts already flagged as suspect, and never sees the runs that sail through looking clean,
which are the ones a miss actually costs you. The cheaper critic passed a fabricated "44%+" target
that the stronger one caught on its first run (`traces/m3-opus-critic-rejection.txt`).

Routing is by risk, computed in code before the call:

| Signal | Model |
|---|---|
| Evidence source never pulled | `claude-opus-5` |
| Brief carried an injection marker | `claude-opus-5` |
| Project carries `confidential` or `launch_hold` | `claude-opus-5` |
| Project has an open `sev-1` | `claude-opus-5` |
| Draft cites a figure absent from the tool results | `claude-opus-5` |
| None of the above | `claude-sonnet-5` |

A routine rejection is still confirmed by `claude-opus-5` before a revision is spent, which is the
one place escalate-on-fail earns its place.

**Known limit.** The signals are structural. The M4 probe fabricated "Deployed and live" and "Rolled
out to all self-serve users", prose claims carrying no figures at all, which the uncited-figure
signal would not catch. That run is covered because `get_activity` was never pulled, but a run with
evidence present and a purely prose fabrication would route to the cheaper model.

## Safety

| Change | What it replaced | Enforcement |
|---|---|---|
| **Confidential guard** | Prompt norms plus the critic's judgement | Code, before validation. Blocks an advancing draft carrying any string the data uses to identify a project flagged `confidential`: id, name, PRD id, or a multi-word descriptor from the name. Widened after review: matching id and name alone passed "the unreleased AI features work", which discloses existence, scope and timing without using either |
| **Sev-1 / launch_hold guard** | Prompt norms | Code. Blocks a green status where the project has an open `sev-1` or a `launch_hold` |
| **Uncited-figure guard** | Nothing | Code. Blocks an advancing draft citing a PR id, issue id or percentage absent from **this project's activity pull**. Tightened after the eval suite: it originally checked the whole source log, so a figure from `search_past_updates` could be presented as this week's. EV-2 caught that three times across 25 runs while the guard passed it, because the guard was looser than the norm it enforces |
| **Proposal rollback** | Nothing | Staged proposals commit only at the human checkpoint. Both cap trips had reported stories as queued from runs that produced no update |

Every guard reads the data rather than a name list. P-PULSAR arrived in a data pack, and a list
written the week before would have passed it silently, which is the same failure as the activity
window that rotted in code.

All three guards run only on the `done` path, so an escalation that names an embargoed project in
order to refuse it is untouched.

### Validating a blocking guard

A guard that blocks a run has one risk that matters more than the rest: a **false positive**, which
pulls a human in for nothing and is how people stop trusting an agent. It cannot be validated by
waiting for it to fire in live running, because it is a backstop for the model failing to refuse and
the model mostly does not. Five live runs produced zero guard fires, which says nothing either way.

`00-build/guard_replay.py` replays every recorded draft through the guards. On its first run it
found two false positives in guards written the same hour:

| False positive | Cause | Fix |
|---|---|---|
| Blocked a draft for "names confidential project P-ORBIT" | The draft mentioned Orbit **in order to exclude it**: "no confidential roadmap items". Complying, not leaking | A mention on a line carrying an exclusion word is compliance |
| Blocked a draft for citing "2%" | That is "+2 percentage points", arithmetic on 41% and 43%, both cited | Percentages derivable from cited figures are allowed |

Two further flags were artefacts of the replay harness, not the guards: evidence was rebuilt from
`get_activity` alone, and past updates were queried by project id when the corpus is keyed on name.
Both made legitimate figures look uncited.

After the fixes, of the recorded drafts that actually reached the guards, **none from the current
data era is blocked**. The single remaining block is a pre-data-pack draft citing #812 and #815,
figures that genuinely no longer exist, which is the guard working rather than misfiring.

This is the same lesson as M2's false stuck, arrived at from a different direction: a check is
easy to write, hard to get right, and the only way to know is to run it against real recorded
behaviour rather than reason about it.

## Measurement

The ledger row is now the structured shape of a run: `project_id`, `iso_week`, `outcome`,
`cost_usd`, `exit`, `tools_called`, `revisions`, `critic_model`, `critic_verdict`, `checks_failed`,
`guards_fired`. Ids, counts and enums only, so the PII constraint in `04-memory-context` §5 holds
without keeping any draft or brief text.

`00-build/stats.py` reads it. Over the first five runs it already showed things no single trace
does:

- **40% of runs reach the critic.** The cheap structural checks stop the rest first, which is the
  cost design working: most escalations never pay for validation.
- **Both validated runs routed to Sonnet.** No risk signal fired.
- **The guards fired for the first time on 2026-09-29**, 11 times in a 300-run eval suite, all of
  them the tightened uncited-figure guard catching drafts that cited a past-updates figure as this
  week's. The ledger recorded none of them until the instrumentation gap above was fixed.
- **The dedupe rule is being broken**, three P-NORTH runs in one ISO week. The in-run warning says
  so each time; the ledger makes the pattern visible.

This is the production-traces stage of the eval lifecycle in `05-bounds-evals` §4, built rather
than described.

## Corrections

| Found | What was wrong | Fix |
|---|---|---|
| 2026-09-29 | **The daily cap was weekly.** `spend_today()` summed the current ISO week, so a bound documented as "$2.00 per day" in `bounds-and-evals.md`, the README and the pitch enforced $2.00 per week for two modules. The contradiction was inside the function's own docstring, "for today's ISO week rows dated today", and nobody read it | Filters on the date in `run_id`. Rows written before `run_id` existed are ignored rather than guessed at |

| 2026-09-29 | **The ledger was blind to guard fires.** The guard-block path was the only `emit_deliverable` call site missing `stats=stats`, and the pre-critic cost cap had the same gap. Neither wrote `exit` or `guards_fired`. The guards fired 11 times in a 300-run eval and `stats.py` would have reported zero | Both call sites pass stats. Verified offline and with a live run |

The second is the sharper of the two. A control worked perfectly and the evidence of it working did
not exist, which is a different failure from a control not working, and harder to notice: a monitor
reporting zero looks identical whether nothing happened or nothing was recorded.

The first differs from the seven documentation-drift instances recorded in
`build-insights.md`. Those were documents falling behind the code. Here the code never matched the
document: the bound was mislabelled the day it was written, and the only symptom was a cap tripping
earlier than expected, which is indistinguishable from a cap working.

## Still open

- **The second-opinion path is unwitnessed in a saved trace.** It has fired once, a routine
  rejection confirmed by Opus before a revision was spent, and the terminal output was not captured.
  It needs a routine critic to reject, which is not reliably forceable, so it stays uncaptured until
  it happens again during ordinary work.

- **Pre-call cost estimate.** The per-run cap refuses the critic call when already over budget, but
  a single expensive drafter turn can still breach it. A token-count estimate before the call would
  let the bound refuse a call rather than regret one.

- **Prose-only fabrication.** No structural signal catches it. Today it is covered incidentally when
  evidence is missing.
- **Paraphrased disclosure.** The confidential guard matches every string the record uses for a
  restricted project, so "the unreleased AI features work" is caught. A paraphrase using none of
  them is not. Closing it needs semantic matching, which means a model call, which is the dependency
  a guard exists to avoid. The norms forbid disclosing existence, scope or timing; the guard
  enforces the names, and critic check 3 covers the rest on judgement.
