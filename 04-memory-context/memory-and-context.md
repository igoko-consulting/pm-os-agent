# Context Engineering & Memory: Cortex PM Chief-of-Staff Agent

> Module 4 · Context Engineering & Memory
>
> ✅ **What this validates:** the agent reasons on the right, safe inputs, by the end you'll have proven a context budget, per-source retrieve-vs-long-context decisions, and a memory map with risk mitigations.
>
> 🗂️ **How the lab maps to this file:** In **Part A** (before the lecture) you don't edit this file, you rough-draft on scratch, focused on the per-source calls in **section 2** plus a quick remember/forget + "how it rots" sketch. In **Part B** (after the lecture) you complete **all five sections**; the Lab Guide's guided builder writes this file for you to copy in and commit.

## 1. Context budget

Every iteration receives, in priority order, most protected first:

1. **Team norms**, whole. Governs everything, and partial norms are worse than none.
2. **Project record and activity** for the project in hand. The evidence the draft is built on, and
   the only thing the update is allowed to cite as fact.
3. **Roadmap confidentiality flags.** Getting this wrong leaks an embargo, which is the one failure
   that cannot be walked back.
4. **The task brief**, fenced as untrusted. Needed to know what was asked, never treated as
   evidence.
5. **Decisions** relevant to this project.
6. **Past updates, for tone.** First thing to drop. A correctly grounded update in slightly wrong
   house style is a far cheaper failure than any of the five above it.

Nothing here is close to the 200K window today. The order matters because it states what gets
sacrificed when that stops being true, and because it puts the brief below the flags: a brief can
ask for anything, and the flags decide what may be said.

## 2. Retrieve vs. long-context: per source

| Source | Size / volatility | Decision | Why, deciding factor in bold |
|---|---|---|---|
| `get_task` | Tiny, new each run | Long-context | One short doc, and it's the instruction itself. Only untrusted input, so it's fenced, never treated as evidence. **Size.** |
| `get_project` | One record, low volatility | Long-context | Small, stable record per run. Barely changes week to week, retrieval machinery costs more than the data's worth. **Size.** |
| `get_activity` | Grows per sprint, high volatility | Retrieve | Split from `get_project` by growth trajectory, not current size. PRs, issues and metrics pile up sprint over sprint, the project record doesn't. **Size.** |
| `search_past_updates` | Unbounded, grows weekly | Retrieve | Unscoped across projects and across content types, since it also reads `decision-log.json`. A narrative aside and a binding decision get pulled with equal confidence. Weakest link in the set. **Size.** |
| `get_roadmap` | Whole file, small | Long-context *(reclassified from Part A)* | Returns the whole file every call, same shape and size as `team-norms.md`, nothing scoped about it. The "must be current" concern is a refetch-every-run policy, not a retrieve-vs-long-context call. **Size.** |
| `get_norms` | Medium, must be current | Long-context | Every run needs all of it, cheap to include whole. Partial norms are worse than none. **Size.** |
| `decision-log.json` | Small now, grows | Retrieve, scoped separately from `search_past_updates` | Decisions are "above the agent line" facts Cortex must honour, not colour commentary from a status update. Sharing one fuzzy retrieval path with `past-updates.json` risks a decision being buried under a status blurb with the same relevance score. **Citation/audit.** |

**Six of the seven are decided by size**, which is what the rubric does when every source is under a
few thousand tokens: the question is settled by growth, not by today's volume. The one row decided
by something else is the `decision-log` split, settled on audit. That asymmetry is the argument for
splitting it out.

**Why this source is the weakest link, precisely.** `search_past_updates` scores on keyword
overlap against each entry's project, summary and theme. On the `missing-data` run the query was
"P-HALO status update", and "status" and "update" appear in nearly every entry's theme, strings like
"status update format, green". So a query about a project that does not exist returned five genuine
matches from other projects. Not a fallback, not an edge case: the two words this agent will use
every single week match everything in the corpus. Cortex ignored the wrong-project hits, by
judgement rather than by rule.

A second, latent bug sat behind it and is now fixed: the function used to return
`hits or corpus[:2]`, so a query matching nothing came back with the first two corpus items labelled
`matches`. It now returns an empty list with `result: "no_matches"`. That one never fired on a real
run, and it would have been indefensible to write a grading check against a tool still capable of
asserting a match it had not found.

## 3. Retrieval quality plan

| Source | Failure mode | Moves |
|---|---|---|
| `get_activity` | Item dates can fall outside the window `get_project` declares. Nothing today checks that a stale PR didn't get bundled in as this week's evidence. | **Document grading:** assert each item's date lands inside the declared window. **Self-verification** (already built): the done-check requires the draft to cite artefacts from this pull. |
| `search_past_updates` | No project filter. A query for a project that isn't even in the corpus, P-HALO in the missing-data fixture, can return another project's figures at the same confidence as a real hit. | **Document grading:** does the hit's project field match the one asked for. **Routing:** precedent and decisions are different questions, split the call. |
| `decision-log` | Shares a retrieval path with `past-updates.json`, so a binding decision scores the same as a status blurb and can lose the ranking. | **Routing:** query it on its own path, the §2 split. **Document grading:** does this decision apply to this project. |

**Reranking and caching are deliberately absent.** Reranking matters when there are many plausible
hits to order; here the problem is that irrelevant ones are returned at all, not that good ones rank
badly. Caching matters when retrieval is slow or repeated; one call per source per week is neither.
Naming why they are not used is worth more than checking them to fill the grid.

**`get_task` is not in this grid and should not be.** Its failure mode is instructions smuggled in
as pasted notes, the jailbreak fixture, and that is not fixed by grading or routing because it is
not a retrieved source. It is fixed upstream, by fencing the brief and treating its content as data
per team norms. Different failure class, different fix. It is carried into §5 as a poisoning risk.

## 4. Memory map (your PM brain)

Cortex currently writes **nothing** durable. Norms, roadmap, project records, past updates and
decisions are all external files it re-reads every run. Nothing it owns can go stale, and equally it
cannot know what it did last week.

| Memory type | What Cortex stores | Scope / TTL |
|---|---|---|
| **Working** (in-loop) | The fenced task brief, tool results, the draft, the validator's verdict, the revision counter, the running cost | This run only. Nothing survives it. |
| **Episodic** (past runs) | Nothing written today. `past-updates.json` and `decision-log.json` are read as episodic memory but are maintained by the team, not by Cortex. **Adding: a run ledger, one row per run.** Constraint, not description: the ledger may hold **only** project id, ISO week, outcome, and cost. No draft text, no brief text, no tool results, no free text of any kind. | Ledger: 12 months, enough to answer "has this week already run". Past updates: read fresh, no cache. |
| **Semantic** (durable facts) | Nothing stored. Team norms, roadmap and confidentiality flags are re-read every run rather than remembered. | No TTL, because there is no cache. Refetch-every-run is the policy, and it is why the roadmap is long-context rather than retrieved (§2). |
| **Shared** (across agents) | The pulled data and the draft, which the validator sees. The drafter's message history and the validator's reasoning stay isolated; the validator's *reasons* flow back on a fail, because that is how revision works. | This run only. Carried from `03-orchestration/orchestration-map.md` §6. |

**Why the ledger, and why only the ledger.** The dedupe rule in `02-loop-design/loop-spec.md` §1 says
one run per project per ISO week, and today that holds only because the draft filename collides. The
ledger is the minimum that makes it real.

It deliberately does **not** store proposal history. The two redundant stories in
`06-autonomy/traces/m4-happy-redundant-stories.txt` were for PRs merged in the same pull, visible in
the run's own context window. That is a context failure, not a memory failure, and a store would not
have helped. Proposal history would help with a different case, a story re-proposed weekly because
nobody actioned it, which is real but not yet observed and is one more thing that can rot. TTLs here
become bounds in M5.

## 5. Memory risks & mitigations

| Risk | Where it bites Cortex | Mitigation |
|---|---|---|
| **Drift** | The norms never said what status colour a quiet week carries. The drafter chose one, the validator ratified it, and it became the rule with no human involved. | Anything the agent settles that the norms do not cover gets surfaced, not absorbed. The only reason this one was visible is that the old behaviour was written into `loop-spec.md` and the new behaviour contradicted it, which is an argument for keeping specs current that has nothing to do with tidiness. |
| **Poisoning** | Two routes. The brief: instructions smuggled in as pasted notes (the jailbreak fixture), and until M3 it reached the validator under the heading "SOURCE DATA Cortex used". Retrieval: "status" and "update" match every project's history, so a query about one project returns another's figures. | Brief fenced as untrusted input, treated as data and never as evidence, per team norms. Document grading on the project field for retrieved precedent (§3). Neither is a defence against a rephrased attack; the actual defence is that no publish, create or merge tool exists. |
| **Staleness** | `ACTIVITY_WINDOW` was a constant in `tools.py`. The data pack moved the activity into July, the constant stayed in June, and the draft printed a window that did not contain its own PRs. Separately, #823 closed #818, making a story Cortex proposed two days earlier obsolete. | Facts live next to the data they have to agree with, not in code: the window now sits on each project record. Document grading asserts activity dates fall inside the declared window (§3). The obsolete-proposal case has no mitigation yet and is named as open. |
| **PII / retention** | Nothing today. The fixtures contain no personal data. Real Jira and Slack carry names, emails and customer identifiers in issue titles and comments, and the episodic ledger would be the first place they would accumulate. | Two controls exist now, both cheap because they are constraints on things not yet built. The ledger schema above forbids free text, so the one store Cortex will own cannot become where PII accumulates. And `BRING-YOUR-OWN-DATA.md` now names the gap at the moment real sources get wired, so the next person hits the question rather than inheriting it silently. Everything beyond that, redaction, detection, retention enforcement, subject access, needs real data to be testable; building it against imagined field shapes would read as coverage while providing none. The 12-month ledger TTL is a number in a document until M5 makes it a bound. |
