# Prototype: Cortex PM Chief-of-Staff Agent

> Module 6 · ★ Deliverable 1, the working agent demo
>
> ✅ **What this validates:** the agent actually runs end to end, by the end you'll have proven it with real screenshots of your Cortex across the six required moments (M2 to M6).

## What it does

_One paragraph: the agent in action, end to end._

## How you built it

- **Coding agent:** _which one you directed (Claude Code / Cursor / Codex)_
- **Model + bounds:** _model used, max iterations, cost cap, queue cap_
- **Repo / config:** _path to your build in `00-build/`_
- **Live link:** _[shareable URL, optional bonus]_

## Screenshots (required, collected M2 to M6)

Real screenshots of *your* Cortex running. These are the `00-build/CORTEX-ANATOMY.md` set and they are required, a link alone is not enough.

| # | Screenshot | What it shows | From |
|---|---|---|---|
| 1 | _[img]_ | happy-path run: a real drafted update + the HITL checkpoint (queued, not posted) | M2 |
| 2 | [`traces/m3-opus-critic-rejection.txt`](traces/m3-opus-critic-rejection.txt) | The critic rejects a draft for a fabricated forward target ("end-of-quarter lift to 44%+") that appears in no tool result, returns a verdict on all six checks, and passes the redraft. Earlier evidence in `traces/m2-critic-rejection.txt`, where the critic caught a claim that stories had been queued when `propose_stories` was never called. | M3 |
| 3 | _[img]_ | a grounded update citing pulled activity + a caught hallucination | M4 |
| 4 | [`traces/m3-jailbreak-tripwire.txt`](traces/m3-jailbreak-tripwire.txt) | The structural rule catching an injection the model ignored silently. Cortex did not flag the SYSTEM OVERRIDE, drafted a clean update and said there were no escalations this week; the code check held the run because an injection marker in the brief requires the escalate exit. See also `traces/m2-jailbreak-refusal.txt`, where Cortex did flag it and still did not escalate, and the critic passed it. | M3 |
| 5 | _[img]_ | an iteration/cost/queue bound halting a runaway | M5 |
| 6 | _[img]_ | end-to-end run | M6 |

## How to run it

_Minimal steps for someone to reproduce the demo (env vars, and the command or the coding-agent prompt you used)._
