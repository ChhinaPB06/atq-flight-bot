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

### E005 recovered observations and E006 enum correction

Recovery run 41578366680 successfully published original source-run 41578099055
JSON on flight-provider-evidence. Recovery green status means evidence transport
only, not successful fares. Stable 0.9.0 returned 8 initial outbounds and 3 paired
results, all rejected by identity validation. Upstream 0.10.0 returned zero initial
outbounds. Source inspection then reproduced an adapter bug: Airport.YYC.value
is "Calgary International Airport", while Airport.YYC.name is "YYC". The newly
added validation compared the human name with the IATA code. Corrected enum
normalization and added real-model regression coverage, plus sanitized identity
fields to future rejection examples. 27 tests pass in each version. Re-run one
pair/version after this meaningful change; add a live-evidence gate to recovery
so recovery alone cannot appear to satisfy live success.

### E006 live retest result and E007 browser hypothesis

Source run 41578488968 evidence is published: both stable and upstream returned
zero initial decoded outbounds on the retest. No new eligible fare yet. This
shows intermittent raw availability; successful initial retrieval on the earlier
runner is not a reliability claim. Enum fix is regression-tested, not live-proven.

New hypothesis from FlightScanner source: ordinary rendered Google Flights can
load results client-side when the HTTP page carries no data. Try standard
Playwright Chromium, using pinned Fli request construction and decoding. One
exact pair, top_n=1, serial page fetches, 10-second spacing, 120-second outer
budget. Observe ordinary page-generated responses; no stealth, replay, proxies,
CAPTCHA/consent solving, or requests after an access denial. Keep this outside
production. Only the browser candidate runs in this experiment; do not repeat
unchanged stable/upstream HTTP queries. Stop if browser is blocked. No claim of
an independent provider: this remains Google with a different normal client.

E007 first runner attempt 41578762803 failed during dependency preparation,
before any browser/provider query. Latest runner image is migrating to Ubuntu
26; Playwright 1.58 targets supported older Ubuntu images. Pin experiment runner
to Ubuntu 24.04 and add safe setup phase/exit-code evidence. This is a platform
compatibility diagnosis to test, not a confirmed explanation without setup logs.
No flight data was obtained and no browser access claim is made.

### E007 observed result and external capability evidence

Source run 41578961275 (Ubuntu 24.04) executed the ordinary rendered-browser
experiment. It decoded 7 initial outbounds; selected-return expansion raised
SearchRejectedError. No complete usable fare was returned. Stop browser requests
on that rejection. Classify explicit rejections separately from generic failures;
added tests for rejection, rate limit and browser denial. No stealth/replay or
challenge-solving fallback is authorized or implemented.

E008 CI inspection run 41579361074 successfully fetched historical logs. Run
41573652801 had 8 accepted Jan25/Apr16 pairs and an empty Jan27/Apr16 search;
41574283529/41574548188 recorded healthy real one-way probes (20/11/15), and
41574548188 had empty Jan27/Apr12 and Jan27/Apr18 paired searches. Initial log
extraction also included unit-test fixture health; fix extraction to accept only
standalone timestamped structured events and test this distinction before using
probe counts as live evidence. This correction does not alter the real 20/11/15
observations or paired search counts.

Runner credential presence checks found no AMADEUS_CLIENT_ID,
AMADEUS_CLIENT_SECRET or TRAVELPAYOUTS_TOKEN (values never read into evidence).
PR creation failure is now diagnosed: repository_disallows_actions_pr_creation.
Do not change that sensitive account setting or retry unchanged PR creation.

Next provider experiment requires an authorized independent source with verified
free live-data allowance and securely configured credentials. Amadeus is a
candidate, not a verified free production entitlement. Sandbox is insufficient.
Asked user for existing provider account name only; never request tokens in chat.
Automatic experiment push trigger removed; no accidental new provider requests.

E008 follow-up: some unit fixtures emitted standalone health lines too. A
standalone-line filter alone was insufficient. Require route identity in every
health probe before admitting it as live-route evidence; the fixture's 12/7/3
has no routes, while actual 20/11/15 has JFK-LHR, YYC-ATQ and ATQ-YYC. Regression
now covers both inline and standalone fixture contamination. Incomplete records
are conservatively excluded, not promoted to verified route health.

## E009 — independent-source eligibility and one public Kiwi observation

User renewed autonomous authorization. Official Amadeus developer-guides source
confirms billing details are mandatory for production and over-quota billing is
automatic (docs/API-Keys/moving-to-production.md). Reject production enrollment
under current no-spending constraint; do not request user billing details.

Try one ordinary Kiwi public website search, independently authored observation
code (no proprietary implementation copied), standard Chromium, one exact pair,
CAD query, 100-second outer limit. Stop on denial/challenge; no retries, login,
stealth, proxy changes or booking. Save only whitelisted public itinerary fields
and schema key/type information, excluding session/booking tokens. This is a new
provider, not another route around the earlier Google denial. Observation never
counts as validated fare retrieval; require explicit response currency, complete
journeys/dates/durations and ticket-type interpretation before accepting data.

E009 actual outcome: source run 41582319498 returned HTTP 403 on the initial
Kiwi page. Provider blocked; no itinerary parsing occurred. Stop this source,
remove automatic push trigger and do not try stealth, proxies or alternate
routes around its denial.

E010: read first-party SerpApi/SearchApi public pricing and Google Flights
response documentation on the authorized runner. No account, credentials,
searches, payment or flight API requests. Select only if a hard free allowance
and required return/currency/duration contract can be verified from those docs.

E010 observed official access evidence: source run 41582497237 retrieved SerpApi
pricing ($0 Free, 250 searches/month) and Google Flights two-stage API docs;
SearchApi advertises 100 free requests/no card but recurring allowance unverified.
Selected SerpApi as an optional candidate, not a live-proven replacement.

E011 implements a Free-account-only optional adapter and one-shot readiness
probe. Enforces account plan and remaining quota before searches, atomic 2-call
reservation, caps of 8/day and 240/month, strict route/date/cabin/CAD/duration and
explicit separate-ticket rejection. Tests remain synthetic until a real key is
available. Production scanner is unchanged. Probe checks existing GitHub secret
SERPAPI_API_KEY; absent key causes credential_missing without network requests.
No production billing, signup or subscription change is performed.

E011 actual runner outcome: 41582782842 reports credential_missing for
SERPAPI_API_KEY. No account/flight request executed. Local stable/upstream test
suites each have 36 passing tests; actionlint passes. Optional integration and
hard local budget are reviewable; live gate remains blocked on a Free account
key. Precise next experiment is the same prepared probe after a meaningful
credential-state change. Do not repeat missing-key runs or enroll a paid plan.
