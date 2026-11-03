# Experiment ledger

Append results with commit, hypothesis, command, budget, evidence, decision and
next action. Never put secret values or raw authenticated request URLs here.

## Baseline inherited at e62e0d1

- Observed local evidence: 24 tests pass for both installed Fli versions;
  repeated SQLite restore/save and stale-writer rejection tested locally.
- User-reported evidence: Actions run 41573652801 had 8 eligible RT results;
  41574283529 had healthy one-way results; 41574548188 had empty RT results.
  These logs remain uninspected by this agent due to API denial.
- Observed live evidence: stable health and pinned exact RT request could not
  reach Google; proxy CONNECT 403. No new flight response exists to parse.
- Decision: no claim of a live retrieval fix. Offline results remain a separate
  gate. Telegram deferred by user's instruction.

## E001 — agent-method selection

- Hypothesis: a committed hypothesis/experiment/evidence loop will prevent
  switching tools without advancing the live retrieval gate.
- Experiment: inspect original autoresearch and Agents SDK primary sources;
  search GitHub for the framework described as Orient/Bilawal Sidhu.
- Evidence: research/FRAMEWORK_REVIEW.md records inspected source revisions,
  applicability and unsuccessful attribution. No inference that framework
  installation changes network access.
- Decision: keep repository agent procedure; do not install additional model or
  GPU runtime. Its effect on live retrieval is unproven until experiments run.

## E002 — pending: transport access after configuration application

- Hypothesis: the current CONNECT 403 occurs before Fli response decoding, so
  changing the parser cannot fix this particular environment failure.
- Prerequisite: observed runtime policy now allows www.google.com, not merely a
  saved draft. Verify status metadata first. Do not repeat requests unchanged.
- Command (upstream venv): `FLI_TIMEOUT=15 timeout 120 python -c 'import tracker;
  report={}; offers=tracker.search_round_trip("2027-01-25","2027-04-16",
  top_n=1,diagnostic=report); print(report); print(offers)'`
- Budget: one initial query plus at most one return expansion, with provider's
  bounded retries accounted for. No batch or outer retries.
- Success evidence: actual decoded response permits separating no outbounds from
  failed return expansion, or real pairs with validated CAD/date/duration data.
- Failure evidence: transport/provider denial remains classified and stops traffic.
- Decision: pending, not executed under unchanged known-denied policy.
- Next: compare same dates under stable after >=10 seconds, then capture sanitized
  fixtures before a parsing/pairing change. Inspect GitHub run logs when API access
  works. Telegram remains outside this immediate experiment.
