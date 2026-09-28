# Optimisations

Changes made beyond the lab's requirements, each with measured before and after. Kept separate from
the module deliverables because none of these were asked for: they came out of running the thing and
noticing what it cost or what it missed.

Numbers are per run on the happy-path fixture, drafter `claude-haiku-4-5`.

## Cost

| Change | Before | After | Why it is safe |
|---|---|---|---|
| **Critic note cap, 25 words** | $0.075 | $0.0552 | Critic output was ~70% of the critic's cost and ~half a run's. Notes are read by a human scanning a verdict; `reasons` still carries the detail on failures. Nothing about what the checks catch changed. |
| **Risk-routed critic** | $0.0552 | $0.0389 | Routine runs validate on `claude-sonnet-5`; `claude-opus-5` is used when the run carries a risk signal. See the routing table below. |
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
| **Confidential guard** | Prompt norms plus the critic's judgement | Code, before validation. Blocks an advancing draft naming a project whose record carries `flags: ["confidential"]` |
| **Sev-1 / launch_hold guard** | Prompt norms | Code. Blocks a green status where the project has an open `sev-1` or a `launch_hold` |
| **Uncited-figure guard** | Nothing | Code. Blocks an advancing draft citing a PR id, issue id or percentage that appears in no tool result |
| **Proposal rollback** | Nothing | Staged proposals commit only at the human checkpoint. Both cap trips had reported stories as queued from runs that produced no update |

Every guard reads the data rather than a name list. P-PULSAR arrived in a data pack, and a list
written the week before would have passed it silently, which is the same failure as the activity
window that rotted in code.

All three guards run only on the `done` path, so an escalation that names an embargoed project in
order to refuse it is untouched. Verified against five cases plus a live run with no false positives:
`traces/m5-guards-and-note-cap.txt`.

## Still open

- **Pre-call cost estimate.** The per-run cap refuses the critic call when already over budget, but
  a single expensive drafter turn can still breach it. A token-count estimate before the call would
  let the bound refuse a call rather than regret one.
- **Ledger metrics.** The ledger records project, week, outcome and cost. Adding exit type, critic
  verdict, which checks failed and revision count would give rejection and escalation rates over
  time, which is the only measure here that improves accuracy rather than cost.
- **Prose-only fabrication.** No structural signal catches it. Today it is covered incidentally when
  evidence is missing.
