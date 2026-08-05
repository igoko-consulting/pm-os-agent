<!--
LAB SPEC — machine-readable. This is the coding-agent runbook and the single source of truth for the Module 4 hands-on lab (the "Part B" polish-and-commit pass; Part A is the pre-lecture, build-by-instinct exercise).
Same steps, same deliverable, same checkpoints — written so a coding harness (Cursor, Claude Code,
Codex) OR a chatbot (ChatGPT, Claude, Gemini) can walk the learner through the graded build. If you are
a human, you can also just read it top to bottom.

NOTE ON PART A: Module 4's hands-on has a pre-lecture "Part A" (ground Cortex + draft the memory plan by
instinct, no rubric yet) in "Module 4 - Lab Guide (Part A).html". Do that first, by hand, and park your
draft. THIS runbook is the graded Part B: defend each call with the rubric, add the retrieval-quality
moves, finalize the memory map, re-run the grounding probe, and commit.
-->

# M4 Lab — Context Engineering & Memory / Part B (coding-agent runbook)

**Deliverable:** `04-memory-context/memory-and-context.md` (context budget · per-source retrieve-vs-long-context · retrieval-quality plan · memory map · risks & mitigations)
**Builds on:** M1 agent-line + M2 loop-spec + M3 orchestration-map + your **parked Part A draft**
**Time:** ~25 min · **Required:** Step 4 (re-run the grounding probe — grounded answer + caught hallucination)

---

## AGENT INSTRUCTIONS — read this first

You are helping a learner **complete this lab, not do it for them.** The per-source calls are theirs.
Rules:

1. **Go one step at a time.** Do not jump ahead or fill later steps.
2. **At every `🚦 DECISION` gate, STOP and ask the learner.** If a retrieved source has *no* agentic
   moves, push back: that's naive RAG — the thing that made Cortex hallucinate.
3. **Never invent their reasoning.** Offer 2–3 options + a recommendation; the learner picks and says why.
4. **When a step says `✍️ WRITE`, update `04-memory-context/memory-and-context.md`** and show the diff.
5. **When a step says `▶️ RUN`, run the command and show the full output.**
6. **At each `✅ CHECKPOINT`, summarise and confirm before continuing.**

> **Works with any assistant.** If your assistant can edit files in your repo, have it **write to
> `04-memory-context/memory-and-context.md`, run the probe, and commit**. If it can't (e.g. plain
> ChatGPT), it **prints the finished block** and you paste it in, then commit. Same deliverable either way.

The build runs on `00-build/fixtures/`; the sources are the real tools in `00-build/tools.py`
(`get_task`, `get_project`, `get_activity`, `search_past_updates`, `get_roadmap`, `get_norms`).

---

## Before you start

Confirm (ask, don't assume):

- [ ] Their forked repo is open; M1/M2/M3 artifacts exist; the build ran in M2.
- [ ] They have their **parked Part A draft** (per-source gut calls + remember/forget + "how it rots").
      If skipped, have them skim Part A first.

---

## Step 1 — Defend each retrieve-vs-long-context call with the rubric  (~7 min)

Run **each source** through the rubric: **size · volatility · citation/audit · cost · latency**. Keep or
flip the Part A call, and get a one-line *why* naming the **deciding factor**.

🚦 **DECISION — per source (from the build):** `get_activity` (large/grows), `search_past_updates`
(unbounded), `get_roadmap` (medium; confidential flags), `get_norms` (medium; must stay current),
`get_task` (one static doc). Retrieve or long-context? Offer the worked-example default, but make them
defend *their* call.

✍️ **WRITE** → `memory-and-context.md` **§1 Context budget** + **§2 Retrieve vs. long-context (per source)**.

✅ **CHECKPOINT:** every source has a decision + deciding factor; the context budget states priority order.

---

## Step 2 — Retrieval quality plan (the agentic moves)  (~5 min)

For every **retrieve** source, 🚦 **DECISION —** which of the five agentic moves its failure mode
demands (not all five everywhere): **routing · document grading · reranking · self-verification ·
caching**.

⚠️ If a retrieved source has **no** move checked, that's naive RAG — at minimum, grade what comes back.

✍️ **WRITE** → `memory-and-context.md` **§3 Retrieval quality plan** (a source × move grid).

✅ **CHECKPOINT:** each retrieved source has at least one agentic move justified by its failure mode.

---

## Step 3 — Memory map + risks & mitigations  (~5 min)

🚦 **DECISION — memory map:** what Cortex stores in **working** (this run), **episodic** (past
runs/threads), **semantic** (durable facts/prefs), and **shared** (across agents) — with a lifetime/TTL
for each.

🚦 **DECISION — risks & mitigations:** cover all four — **drift**, **poisoning**, **staleness**,
**PII/retention** — each with where it bites Cortex and the mitigation. (This is where the A3 "how it
rots" sketch gets real.) Tie read/write scope back to the M1 agent line and TTLs forward to M5 bounds.

✍️ **WRITE** → `memory-and-context.md` **§4 Memory map** + **§5 Memory risks & mitigations**.

✅ **CHECKPOINT:** four memory types scoped with TTLs; all four risks have mitigations.

---

## Step 4 — Re-run grounding to match the plan  (REQUIRED, ~5 min)

Make the retrieve-vs-long-context distinction real in the build.

1. ▶️ **RUN the happy path** (`python agent.py`) and point out the **exact pulled data** each claim came
   from (a retrieve source like `get_activity`/`get_norms` that Cortex must *cite*; the task itself as a
   long-context source).
2. ▶️ **RUN the probe:** withhold a source Cortex needs (remove `get_activity`, or run
   `python agent.py missing-data`). A well-grounded Cortex says "I can't verify that" or escalates
   instead of inventing — and the critic catches an invented metric.

📸 **CAPTURE (required):** two states — (a) a grounded answer citing pulled data, and (b) the
withheld-source case where Cortex refuses/gets caught — into `06-autonomy/prototype.md` with captions.

3. ▶️ **Commit + push** `memory-and-context.md`.

✅ **DONE when:** all five sections are filled, the grounding capture is saved, and everything is committed.

---

## 💼 In practice

This is the module that decides whether your agent is confidently wrong or reliably right. "Retrieve vs.
long-context per source" is the call that keeps costs sane and answers grounded — and it's exactly the
conversation you'll have with engineers building any RAG or agent feature. The memory risks (drift,
poisoning, staleness, PII) are the ones that surface six months after launch when a stored fact goes
stale or a bad input gets trusted forever. A PM who can point at *why* each source is retrieved and *what*
the agent forgets and when is the one who prevents those incidents.

---

## Done-check (verify before saying "complete")

- [ ] `04-memory-context/memory-and-context.md` has all five sections **in the learner's words**.
- [ ] Every source has a retrieve/long-context decision with a named deciding factor.
- [ ] Every retrieved source has at least one agentic-retrieval move (no naive-RAG rows).
- [ ] Memory map covers working/episodic/semantic/shared with TTLs; all four risks have mitigations.
- [ ] The required grounding capture (grounded + withheld-source) is in `06-autonomy/prototype.md`.
- [ ] Everything is committed and pushed.

**Debrief (post in `#cohort-channel`):** your trickiest retrieve-vs-long-context call and the single
rubric factor (size, volatility, citation, cost, or latency) that settled it.

**Next:** Module 5 — Bounds, Trust & Evals: make it fail safe and prove it.

*Product School · Agentic Loops for PMs · M4 Lab / Part B (coding-agent runbook)*
