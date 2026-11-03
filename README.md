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

The tested code is on **main**. The `Personal YYC–ATQ Flight Watch` Actions workflow
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
- **45offline tests** and actionlint pass. Tests alone are not live fare proof.

Inspect Actions summaries, LIVE DIAGNOSTIC, COVERAGE, saved history and the
flight-provider-evidence branch. Run `python tracker.py status` against a restored
current DB for current best/coverage. Research and failures are documented in
[PROJECT_STATUS.md](PROJECT_STATUS.md) and [research/EXPERIMENTS.md](research/EXPERIMENTS.md).
Earlier log sections describe superseded scopes and blockers. No automated PR was
created because repository policy disallowed Actions PR creation; normal
fast-forward main activation was used for the user's requested live schedule.
No force push or account-permission change occurred.

Latest operational checkpoint:20/54pairs checked,19with usable quotes and1no-data result;34remain. BestobservedCAD2074 Jan29–Apr21,82days,30h10outbound/28h22return. PreferredJan27 bestCAD2233 returningApr23. Run41590235586 correctly marked degraded for the no-data pair while preserving all progress; rollinghour quota then deferred further checks. The active four-hour schedule continues remaining work. These prices are not checkout-confirmed.
