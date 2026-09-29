# Build Insights: Cortex PM Chief-of-Staff Agent

> Module 6 · ★ Deliverable 5, what building this actually taught me

## One friction

Documents drifted from the build in every module. Seven instances across six modules: a critic model
decided in M1 and still unwired in M3, a run ledger that two deliverables described in the present
tense and that did not exist, stop conditions listing none of the four exits built that day, a
failure-mode register calling a shipped guard "proposed", an anatomy sketch still showing
placeholders for three artefacts that existed, a ledger constraint enumerating four fields when it
carried thirteen, and a claim that redundant story proposals were undetectable after the tool that
detects them was built.

Not one was carelessness. Every one was correct when written, and stopped being correct because
something downstream changed.

An eighth was different and worse. The daily spend cap was never daily: it summed the ISO week, so a
bound documented in three places as "$2.00 per day" enforced $2.00 per week for two modules. That was
not drift. The code never matched the document, from the day it was written, and the only symptom
was a cap tripping earlier than expected, which is indistinguishable from a cap working. A document
that is wrong is findable by reading. A control that quietly does something other than what it says
is only findable by measuring it.

Nothing fails when a document is wrong, so the only way to find drift is to go looking. It never
felt like the main work, yet it produced more corrections than testing did. This is a governance
problem. A document nobody can trust is not a control.

## What I now understand about shipping agents

**A bound is only real if it is in code.** Anything held by prompt text is a suggestion. The
strongest control in the system is a tool that does not exist: Cortex cannot post because there is
no publish function, and no prompt injection changes that. The two risks I ranked worst were held by
norms and a second model until I moved them into code in the last module.

**Inconsistent behaviour is usually a spec problem.** Six runs across three modules flip-flopped
between inventing story IDs and refusing to. I logged it as model variance twice. It was a missing
tool. The brief asked for something the tool surface could not supply, so inventing and refusing
were both rational answers. No prompt tuning would have fixed it.

**A wrong check costs more than no check.** My definition-of-done check marked a correct draft as
stuck, twice, for two different reasons. My safety guard blocked a draft for naming a confidential
project when the draft named it to exclude it. Each time the agent was right and the check was
wrong. False alarms teach people to stop reading alarms, and that removes the control.

## The aha

Writing the plan found more defects than running the build:

- Every ROI metric had no data behind it. The ledger recorded what the agent did and nothing about
  what the human thought
- A model outage killed the run with a stack trace and no escalation
- The loop spec's dedupe rule had no state to dedupe against

None came from a failing run. They came from writing down what should be true and noticing it was
not.

The ledger gap matters most for scale. Without a human verdict on each run, cost cannot be tied to
value, so there is no business case for a second team.

## Cost and scale

Cost is bounded on three fronts. A per-run cap, checked between turns and again before the critic
call because that is the largest single spend. A daily cap, checked before a run starts, which is
the only genuinely hard one since it refuses rather than halts. And an iteration cap, which stops a
loop spending forever even when each turn is cheap.

The per-run cap is still not hard, because a call's cost is only known after it returns. The next
step is a pre-call estimate from the token count, so the bound refuses a call instead of regretting
one.

A halted run also discards its staged stories, so a stopped run leaves nothing queued.

## What I'd do differently

Write the eval cases in Module 2, not Module 5. I built checks for four modules with nothing to
validate them against, which is how two of them shipped wrong. The replay harness that caught the
guard false positives took twenty minutes and would have worked from the first module.

Running the suite for the first time proved the point twice over. Its first report claimed 50/50 on
two cases; 36 of those runs had never started, because the daily spend cap had stopped them and the
check "did not advance" is trivially satisfied by a run that never began. An eval that cannot tell a
non-run from a pass is the same fault as a done-check that cannot tell a missing evidence source
from a quiet week, and I wrote both.

The second attempt ran out of prepaid credits at pass 12. Both stops were the spending controls
working. It also showed that the gate I wrote in Module 5 is unaffordable inside the bounds I wrote
in Module 5: 50 passes cost about $6 against a $2 daily cap. Neither number was wrong on its own.
Nobody had checked they were compatible, because nothing had been run.
