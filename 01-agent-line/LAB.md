<!--
LAB SPEC — machine-readable. This is the coding-agent runbook and the single source of truth for the Module 1 hands-on lab.
Same steps, same deliverable, same checkpoints — written so a coding harness (Cursor, Claude Code,
Codex) OR a chatbot (ChatGPT, Claude, Gemini) can walk the learner through it. If you are a human,
you can also just read it top to bottom.
-->

# M1 Lab — The Agent Line (coding-agent runbook)

**Deliverable:** `01-agent-line/agent-line-map.md`
**Builds on:** nothing yet — this is the first lab; it seeds every later module
**Time:** ~25 min (+ one-time build setup) · **Required:** Step 0 (get the build running once)

---

## AGENT INSTRUCTIONS — read this first

You are helping a learner **complete this lab, not do it for them.** The scoring and the line they draw
are theirs. Follow these rules:

1. **Go one step at a time.** Do not jump ahead or fill later steps.
2. **At every `🚦 DECISION` gate, STOP and ask the learner.** If they drop an action below the line
   "because the agent can do it well", push back once: *capability is not permission.*
3. **Never invent their reasoning.** Offer 2–3 options + a recommendation; the learner picks and says
   why. Record *their* words.
4. **When a step says `✍️ WRITE`, update `01-agent-line/agent-line-map.md`** and show the diff.
5. **When a step says `▶️ RUN`, run the command and show the full output.**
6. **At each `✅ CHECKPOINT`, summarise and confirm before continuing.**

> **Works with any assistant.** If your assistant can edit files in your repo, have it **write to
> `01-agent-line/agent-line-map.md` and commit**. If it can't (e.g. plain ChatGPT), it **prints the
> finished block** and you paste it in, then commit. Same deliverable either way.

**Default posture:** every decision starts **above the line** (human owns) and must *earn* its way below.

---

## Step 0 — One-time build setup  (REQUIRED, ~10 min)

You will run a real Cortex from M2 onward. Set it up now so you never have to hand-write code.

1. On GitHub, use the **`run-your-ai-agent-team-template`** repo (**Use this template → Create a new
   repository**) and open your copy in your coding agent.
2. ▶️ **RUN setup:** install deps and wire the key. Use the **Setup** prompt in
   [`00-build/PROMPTS.md`](../00-build/PROMPTS.md), or:
   `cd 00-build && pip install -r requirements.txt && cp .env.example .env` (macOS: `python3`/`pip3`).
3. Add your model API key to `00-build/.env` and **set a hard spend cap** (in `.env` and in the provider
   dashboard). This cap is the first bound you'll formalize in M5. Never commit `.env`.
4. ▶️ **RUN a smoke test:** `python agent.py` in `00-build/` — confirm a clean happy-path trace prints.
5. Skim [`00-build/CORTEX-ANATOMY.md`](../00-build/CORTEX-ANATOMY.md) — the seven things every submission
   must show.

✅ **CHECKPOINT:** `python agent.py` produces a clean trace and the `.env` (with a spend cap) is set and gitignored.

---

## Step 1 — List every discrete decision/action  (~5 min)

Break Cortex's workflow into its smallest meaningful units (aim for **6–8**). A "decision" is any point
where something gets *decided* or *done*. If an item bundles two risk levels (drafting *and* sending),
split it — the line is drawn between atomic actions.

Offer this starter list; the learner prunes/extends: pull project state + activity · decide relevant
context · draft the update · decide tone/commitment level · flag at-risk/escalation · choose what to
escalate · propose a story batch (capped) · post an update / approve a company-wide one.

✅ **CHECKPOINT:** 6–8 atomic actions listed.

---

## Step 2 — Score each on the three axes  (~6 min)

For every item, mark **High/Med/Low** on: **Reversibility** (how easily undone if wrong), **Blast
radius** (damage before someone catches it), **Measurability** (can we tell after the fact if it was
right). Be honest, not optimistic.

✍️ **WRITE** → `agent-line-map.md` **The workflow, decision by decision** table (with the three scores).

✅ **CHECKPOINT:** every action has three honest H/M/L scores.

---

## Step 3 — Place each above or below the line  (~4 min)

🚦 **DECISION — apply the golden rule per item:**
- High reversibility + low blast radius + high measurability → **below** (Cortex owns).
- Low reversibility, OR high blast radius, OR low measurability → **above** (human owns) or **HITL**.
- Borderline ("Med" that could swing) → **HITL**: Cortex does the work, a human approves. Most of the
  real product design lives in these checkpoints.

✍️ **WRITE** → add the **Above/Below** and **HITL?** columns to the table.

✅ **CHECKPOINT:** every action has a verdict; borderline ones are HITL, not forced binaries.

---

## Step 4 — One-sentence justification + anatomy + hardest call  (~5 min)

1. For each decision, ✍️ **WRITE** a single sentence naming the deciding axis:
   *"<Decision> sits below/above the line because it's <reversibility> to reverse, has a <blast radius>,
   and is <measurability> to verify — deciding factor: <axis>."*
2. ✍️ **WRITE** → the **Agent anatomy (sketch)** (model + when you'd escalate to a frontier model, tools,
   memory; loop/bounds/evals stay placeholders for later modules).
3. 🚦 **DECISION — the hardest call.** The above-vs-below decision they went back and forth on, and the
   single axis that settled it. ✍️ **WRITE** → **Hardest call**.
4. ▶️ **Commit + push** `agent-line-map.md`.

✅ **DONE when:** the map has the scored table with verdicts, per-decision justifications, the anatomy
sketch, and the hardest call — all committed.

---

## 💼 In practice

The agent line is the first thing to draw for *any* AI feature, not just this course. It's how you answer
the question every exec and security reviewer asks: "what can this thing do on its own, and what still
needs a human?" Drawing it *before* you build stops the most common failure — shipping an agent that can
do something impressive in a demo and something catastrophic in production. "Capability is not
permission" is the sentence that keeps you employed.

---

## Done-check (verify before saying "complete")

- [ ] The build runs (`python agent.py` gave a clean trace) and `.env` + spend cap are set.
- [ ] `01-agent-line/agent-line-map.md` lists 6–8 atomic actions, each scored on all three axes.
- [ ] Every action has an Above/Below/HITL verdict and a one-sentence justification naming the deciding axis.
- [ ] The anatomy sketch + hardest call are filled in the learner's words.
- [ ] Everything is committed and pushed.

**Debrief (post in `#cohort-channel`):** your hardest above-vs-below call and the single axis that settled it.

**Next:** Module 2 — Loop Engineering: turn the hand-off into an agent that fires itself.

*Product School · Agentic Loops for PMs · M1 Lab (coding-agent runbook)*
