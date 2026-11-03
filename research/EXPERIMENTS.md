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

## E003 — alternative-provider contract audit

- Hypothesis: a maintained replacement can supply both directional durations,
  returned CAD currency and a complete RT price without paid infrastructure.
- Experiment: clone and inspect five public candidate implementations and licenses;
  compare their actual parser/result contracts. Inspect source, not star count.
- Evidence: PROVIDER_COMPARISON.md records exact revisions and shortcomings.
  FlightSearcher synthetic multisegment input with 2100-minute total outputs
  only the first 60-minute segment in both directions. Not a live test.
- Decision: reject those candidates as immediate drop-in replacements; retain
  Fli provisionally, Amadeus as a credential-dependent independent candidate.
  No evidence of a fully satisfying independent free live source yet.

## E004 — identify the Fli expansion boundary

- Hypothesis: tracing decoded initial and selected-return pages can distinguish
  empty initial data from failed expansion, without changing pairing semantics.
- Experiment: subclass the pinned _fetch_flights boundary; run real Fli expansion
  logic with one controlled outbound followed by an empty selected-return result;
  compare with empty initial response and transport exception cases.
- Evidence: tests/test_provider_trace.py; all 26 offline tests pass under both
  provider versions. Exceptions preserve stage metadata for durable diagnostics.
- Decision: keep instrumentation; it does not fix or prove live retrieval.

## E005 — pending: GitHub-hosted execution and evidence return

- Hypothesis: intended GitHub runner can execute a bounded live comparison even
  though the cloud machine cannot access Google or the GitHub API.
- Experiment: provider-experiment.yml runs on development-branch workflow/script
  push only, tests one pair per provider version, top_n=1, 120-second outer timeout,
  library retries bounded, 10-second pause. Saves sanitized JSON on a separate
  flight-provider-evidence branch with ordinary fast-forward push plus artifact.
- Command: push workflow commit; use git ls-remote/fetch/show to inspect evidence.
- Acceptance: only usable_live_quote with real validated fare fields advances the
  live gate; empty/blocked/unrun remains failure/inconclusive. No notifications,
  production DB mutations or paid services. API/CI availability is not assumed.

### E005 first remote outcome and evidence recovery

- GitHub HTML pages expose run metadata despite API denial. Offline matrix run
  41578099204 passed both versions. Live experiment 41578099055 ran and failed;
  its evidence publishing step failed separately with exit 3. Logs require login.
- Publishing defect diagnosed from code: including checkout config defines origin
  before remote add, causing duplicate-remote failure. Corrected operation order.
- Recover the existing artifact through Actions' scoped token, then publish it;
  RECOVER_RUN_ID is pinned to the original run. This avoids repeating flight
  requests just to repair evidence transport. Recovery success is not live success.
- Also corrected an earlier job-level runner.temp expression rejected by GitHub
  (run 41578097686). Use GITHUB_ENV at step runtime instead. Official actionlint
  v1.7.7 release checksum verified; all three workflows pass its expression check.
