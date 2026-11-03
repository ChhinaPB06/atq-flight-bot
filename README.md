# Personal YYC–ATQ flight monitor

Tracks **54 valid round-trip date pairs** for one adult in economy:

- Depart Calgary **January 27–31,2027**, preferring January27.
- Return **80–90days after departure**, no later than **April30,2027**.
- Both whole journeys must be **31hours or less, including layovers**.
- CAD pricing; target **$1600**, alert threshold **$1900**.
- Record qualifying higher-priced fares for history too.
- No airline, stop-count or US-transit exclusion. No booking or payment.

January31 plus90days isMay1 and is excluded, hence54rather than55pairs. Day counts
are between outbound departure and return departure dates, matching the date grid.
They do not independently measure nights spent after arrival in India.

## Current operation

The scheduled API scanner is deployed on **main**. The `Personal YYC–ATQ Flight Watch` Actions workflow
runs on cron `23 */4 * * *` (every4hours). GitHub may delay scheduled execution.
Workflow configuration changes on main can also start one operational run.
Ordinary source/documentation pushes do not issue flight searches.

The maintained API source is **SerpApi Google Flights**. It checks the account is
`plan_id=free` with a zero-dollar monthly price before querying. Returning flights
require selecting an outbound with a departure token; the monitor checks actual
returned routes, dates, economy cabin, server-returned CAD parameters and complete
journey durations. It uses the selected-return price, not a sum of independent
one-way quotes. Explicitly labeled separate-ticket results are rejected from this
round-trip acceptance path. This is a provider search quote, not a guarantee of a
single airline ticket, availability at checkout, bags or final seller charges.

Durations use the greater of the provider's whole-journey total and elapsed time
reconstructed from YYC/ATQ airport-local endpoints and timezones. This conservative
check includes layovers; it never merely sums flying times.
Both the scanner and audit explicitly load pinned `tzdata==2026.6` (IANA2026f),
instead of relying on potentially different host OS rules. This matters because
older Calgary winter rules differ from the current rules for January2027.

## Free quota and whole-grid coverage

SerpApi's current [Free plan](https://serpapi.com/pricing) advertises250searches/month.
A complete pair check costs up to2searches. The bot reserves2before requests,
retains reservations after ambiguous failures, and stores them with durable history.

- Initial pass: up to **18pairs per trigger**, at most40searches/rollinghour,
  120/day and240/month, and never beyond the provider's remaining allowance.
- Initial54pair pass costs at most108searches. It needs multiple triggers and can
  be deferred by quota, provider errors or GitHub scheduling. An attempted pair
  is not necessarily a nonempty or qualifying result.
- After initial attempts finish: at most **2pairs/day** under4searches/day, with
  the same rolling-hour and monthly caps. This keeps ongoing monitoring within
  the free allowance after the initial research pass.

**Every4hours means a workflow trigger, not a fresh search of all54pairs.** The
Free plan cannot support648searches/day needed to check54pairs six times daily.
Coverage output separates cumulative attempts, nonempty responses, valid-priced
pairs and remaining first-pass work. Older out-of-scope metadata is archived;
all prior observations are preserved and excluded from current-scope percentages.

## Credentials and local development

GitHub Actions secret **SERPAPI_API_KEY** is required. A Free-plan key is configured
and has passed live validation. Never put keys in source, issue bodies, reports or
chat. No paid subscription, billing enrollment or upgrade is performed by the bot.

For local use, provide the key through your secure environment and use Python3.12:

```sh
python3 -m venv /workspace/venvs/atq-flight-bot
. /workspace/venvs/atq-flight-bot/bin/activate
pip install -r requirements.txt
export FLIGHT_PROVIDER=serpapi
export FLIGHT_DB=/workspace/atq-flight-bot-local/fares.sqlite3
export FLIGHT_DISABLE_ALERTS=1
python -m unittest discover -s tests -v
python tracker.py pairs
python tracker.py scan --dry-run
python tracker.py health
python tracker.py status
# This consumes Free allowance and writes history:
python tracker.py scan
```

`health` checks API account access/free plan/quota; it explicitly does not prove
route availability. A real detailed scan is needed for that. Default direct CLI
provider remains Fli unless FLIGHT_PROVIDER=serpapi is set; Actions sets it.
Fli is retained for source research and the independent two-version test matrix,
not selected as the production source after intermittent/blocked paired results.

## Persistence and failure interpretation

Actions restores SQLite from the **flight-data** branch and saves with SQLite's
backup API plus an integrity check. Ordinary fast-forward pushes preserve code
history and avoid rebasing binary databases onto main. Concurrency serializes
writers; a stale push fails visibly instead of overwriting newer history. A
14day recovery artifact is retained. Never reset history silently if restoration
or integrity fails; investigate and recover the latest known-good copy.

Tables retain observations, diagnostics, active54pair metadata, archived old
metadata, initial-pass attempts, quota reservations and audit operations. Persist
all of them together. Development should use FLIGHT_DB outside the tracked seed DB.

Provider data absence, rejection/blocking, rate/quota limits, parser/identity
failures, duration rejection and above-threshold quotes are distinct outcomes.
Empty responses do **not** prove zero flights. API errors stop the run; quota
exhaustion is explicitly logged as no new live verification. A batch with empty
or rejected searches is marked degraded even when other dates produced quotes.
Provider diagnostics include bounded rejection reasons. Blocked/rate-limited,
timeout and parser errors remain distinct. Only continuous connected journeys
with valid airport-local timestamps are accepted; same-airport layovers cannot
depart before arrival. A failed refresh clears the current price while retaining
earlier observations, and failed initial queries rotate behind unchecked dates.

History backup reads the source without creating it, rejects missing/corrupt or
schema-less databases, validates a temporary copy and replaces the destination
atomically. The scheduled job will not save after a failed restore.

## Telegram (currently deferred)

Research/scheduled operation currently sets FLIGHT_DISABLE_ALERTS=1. No Telegram
messages were sent during live integration tests. When the user chooses to enable
notifications, configure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in GitHub Actions
secrets, dispatch `test-telegram` once, then change the disable flag to0.

Alerts include source, CAD price, dates, both total durations, observation time,
search link and checkout limitation. Successful duplicate itineraries alert again
only after a price drop of at leastCAD100. Failed deliveries are not deduplicated
away. No quote is checkout-verified automatically. The manual `confirm` command
records only the user's reported checkout observation, never an independent check.

## Verified evidence and maintenance

- Source run41584121588: two real scans; restored history12→13→17observations,
  integrityok and quota reservations2→4.
- Source run41588472235: narrowed54pair grid; both live scans succeeded;
  history17→21→25, reservations4→6→8.
- Source run41589012699: initial3pair batch and history persistence succeeded;
  active first-pass coverage6/54 before the main sweep.
- Best observed at that checkpoint: **CAD2245,Jan27–Apr20**,83days,
  **25h25m outbound /28h10m return**, search quote only. New scans may change it.
- **88offline tests** pass locally under stable and upstream after the specialist
  review; current remote validation is recorded in PROJECT_STATUS.md. The earlier
  58test baseline passed remoteCI41656960169. Tests alone are not live fare proof.

Inspect Actions summaries, LIVE DIAGNOSTIC, COVERAGE, saved history and the
flight-provider-evidence branch. Run `python tracker.py status` against a restored
current DB for current best/coverage. Research and failures are documented in
[PROJECT_STATUS.md](PROJECT_STATUS.md) and [research/EXPERIMENTS.md](research/EXPERIMENTS.md).
Earlier log sections describe superseded scopes and blockers. No automated PR was
created because repository policy disallowed Actions PR creation; normal
fast-forward main activation was used for the user's requested live schedule.
No force push or account-permission change occurred.

## Reproduce the complete coverage audit

Use the read-only report of every active date pair:

```sh
python scripts/coverage_report.py --db /path/to/restored/fares.sqlite3 --csv /path/to/54-pair-results.csv > /path/to/coverage-audit.json
```

It reports exact date-grid membership, cumulative attempts, quote timestamps,
four-hour quote freshness, provider/status, CAD prices, durations and search links.
Current-usable price/confidence means the most recent recorded attempt, not a
new quote at report-generation time. Historical prices remain explicit after
failed refreshes; invalid stored quotes cannot count as valid or fresh.
It independently rechecks stored API quotes against currency, route/date,
connection and elapsed-duration constraints. It issues no provider request and
does not modify the database or spend credits. A successful audit validates stored
facts; it does not mean every pair has a quote, all prices are fresh, Telegram
worked, or checkout was confirmed.

The native email pilot is a manual prototype, separate from the scheduled
API scanner. Its tests use synthetic messages. Actual Google alert
ingestion and all 54 native watches have not been demonstrated. Follow
[the pilot setup](research/NATIVE_ALERT_PILOT.md) for the required real sample;
no mailbox connector or recurring inbox ingestion is currently configured.

Latest completed initial pass: **54/54 pairs attempted**, **44 with usable fares**,
five provider-empty/unverified and five with returned fares rejected by validation.
Run41654025980 added31observations (116→147), preserved previous history, and
saved an intact database. It correctly failed as degraded for the unusable results.
An audit of134active-pair APIobservations under pinned current rules found no
invalid stored quote. Best observed remainsCAD2074 Jan29–Apr21,82days,
30h10outbound/28h22return, observed2026-11-03at06:31:27UTC, not checkout-confirmed.
This is cumulative coverage; only25pairs had quotes observed within4hours at the
14:37UTCsnapshot. Five empty responses do not prove unavailable flights, and
five filtered responses concern the selected outbound's return options, not an
exhaustive rejection of every possible airline itinerary for those dates.
