# YYC–ATQ personal flight hunter (Level 2, free-first)

A **personal-only**, no-paid-API prototype for tracking YYC–ATQ return flights. Not a commercial product or a checkout bot.

## What it does

- Enumerates **every** eligible Jan 25–31, 2027 departure and 60–90-night return combination (returns no later than Apr 30): **216 pairs**.
- Prioritizes Jan 27 and returns around Apr 15, while continuing to rotate through all stays.
- Each scheduled run queries the **Fli** flexible-date calendar for two previously least-checked stay lengths. When the calendar returns a quote, it marks the pair as `price_observed`; if no quote is returned, it marks `no_quote`, **not** "no flights".
- Does **one** live round-trip search per scheduled run, selected from promising calendar results. Both journeys must have total journey durations **≤1,860 minutes**. Explicitly requests CAD currency for calendar and live searches. Reports CAD prices as *live-search observed*, **not checkout confirmed**.
- Saves fare observations and alerts in a durable SQLite file. Telegram alerts for fresh fares ≤CAD 1,900, with priority at ≤CAD 1,600. Deduplicates repeat alerts unless price drops ≥CAD 100.
- GitHub Actions runs every 4 hours on a schedule; exact timing is not guaranteed. All software is free/open source; the unofficial Fli source can fail, become unavailable, or have usage restrictions.

**Critical honesty:** With two duration-calendar calls per run, scanning all 31 stay lengths takes about 16 runs (~2.7 days), not every four hours. The calendar itself may omit some pairs. Live search does **not** verify 216 pairs every four hours. The bot cannot automatically prove the final seller checkout price. Only a manual user-entered prepayment total is labeled `user_confirmed_checkout`. Those restrictions matter even though this is a Level 2 scheduling and tracking prototype.

## Getting started

1. Create an empty **private** GitHub repository and upload these files. GitHub connector did not reveal an accessible repo during construction, so no push has been made.
2. On GitHub: **Settings → Actions → General → Workflow permissions → Read and write**. The workflow commits the SQLite file to the private repo after each scan. GitHub scheduled workflows require the workflow on the default branch.
3. Create a free Telegram bot with `@BotFather`, then send it a message and retrieve your numeric chat ID via Telegram's `getUpdates` endpoint. Do not paste bot tokens into source control.
4. In GitHub repository Settings → Secrets and variables → Actions, create `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.
5. In GitHub **Actions**, run `Personal YYC–ATQ Level 2 Flight Watch` manually once. Review output and check Telegram.
6. On any computer with Python 3.11+: `pip install -r requirements.txt`, `python tracker.py scan --dry-run`, `python tracker.py status`, `python -m unittest discover -s tests -v`.

## Commands

```sh
python tracker.py pairs          # all 216 eligible pairs
python tracker.py scan --dry-run # next rotation, no requests
python tracker.py scan           # run discovery + live search
python tracker.py status         # coverage and lowest quotes
python tracker.py confirm --depart 2027-01-27 --return-date 2027-04-15 --price 1580 --seller-url https://example-airline.com/review
```

The `confirm` command records only **what you manually reported seeing** on a final pre-payment page. No ticket is purchased and no one should assume a fare is held.

## Free access / safety / limitations

- Fli: https://github.com/punitarani/fli (third-party MIT Python library). The Google Flights access method is **unofficial and reverse engineered**, not a Google-supported public API. Use it only where permitted; do not bypass blocks, CAPTCHAs, or access controls. If search errors persist, stop and use normal Google Flights price alerts or an authorized provider.
- GitHub Actions: free plans have quotas, scheduled executions can be delayed, private repo minutes are metered, and workflows can become disabled after long inactivity. Six 20-minute worst-case runs per day could exceed typical free allowances, so the default is only three queries per run and modest runtime. Check actual billing/usage.
- Git history holds fare history after state commits; in a private repository only. No tokens stored in SQLite. GitHub credentials and Telegram credentials are stored in Actions Secrets.
- Airline-specific checkout automation is **not included**. Price on a search page can change; bags, payment method, transit/visa rules, and seller terms need to be checked personally.
- Fli API objects and Google’s search internals may change. On an incompatible release, inspect the workflow log and adjust the provider adapter; the tests are offline and do not prove live operation.
- Some round trips may not be visible because Fli expands a limited number of outbound options. Do not interpret a missing result as an absence of flights.

## Design notes

Files: `tracker.py` contains the date-grid, SQLite schema, calendar and live Fli adapters, fare filters, Telegram alerts and CLI. `.github/workflows/flight-watch.yml` runs scheduled jobs. `tests/` contains offline unit tests.

To reduce site traffic, the default rotates through two stay lengths and one date pair per four-hour execution with a 10-second pause. To accelerate discovery during manual testing, override `--calendar-per-run` (max 31), but avoid excessive query bursts.

## Research and maturity notes (November 2026)

The implementation uses **Fli** only as its external flight-search engine, plus Python standard library, SQLite, Telegram Bot API and GitHub Actions. Design ideas were inspected from `klebermc/FlightScanner` (exhaustive date pairs), `ostrvcxztd/flightsearch` (cheap cached discovery), and `derekcheungsa/flight-monitor` (historical views), but **their code is not bundled**. `AWeirdDev/flights` is an alternative provider, not installed in the current bot. Multiple free GitHub repositories do not multiply the quota of a shared upstream provider.

**No live Fli test has been performed here:** the environment used to package this project does not have `flights` installed and no external ticket-checkout session was performed. The seven tests validate offline behavior only. A GitHub deployment is not active until you create a repository and configure it; the connected GitHub account returned no accessible personal repositories at build time.

**Price labels are strict:** calendar results are *discovered*, Fli round-trip results with both durations are *live-search observed*, and `confirm` saves a *user-reported* checkout price; it is not independent automated checkout confirmation. A future separately verified provider or permitted browser checkout integration would be needed to independently confirm that last price.

## Diagnostic update (Nov 2026)

The live search now expands five outbound candidates and logs a JSON `LIVE DIAGNOSTIC` with raw returned pair count, eligible count, and rejection reasons: missing/invalid total price, missing duration, over-31-hour outbound/return/both, and unexpected provider data structure. A provider exception fails the job instead of masquerading as a successful search. `empty_response` does **not** prove there are no flights. Two live date-pairs are checked per four-hour run, so 216 independent live searches still take at least ~18 days with six runs per day (if no dates are prioritized again), not four hours. Calendar coverage is separate and faster. The full checkout price remains manually verifiable only.

---

## Phases 1–4: Provider health, alternative source, complete coverage, and alert validation

This release adds a **provider-health gate**. A green job means the search was not silently broken; a red `SCAN DEGRADED` status means investigate logs, not "no flights". The source can still miss offers even when healthy.

### Phase 1 — Prove the Fli source works

Every scheduled scan compares these one-way source probes:

- `JFK → LHR` Jan 27, 2027 — busy control route (must return itineraries to establish basic search health).
- `YYC → ATQ` Jan 27, 2027 — actual outbound direction.
- `ATQ → YYC` Apr 15, 2027 — actual return direction.

Read the `PROVIDER HEALTH` line. `provider_unhealthy_or_blocked` does **not** mean no flights exist. `one_way_routes_healthy` establishes only one-way parsing/availability for the sample dates; the two subsequent detailed round-trip searches are a separate check. The `LIVE DIAGNOSTIC` line reports raw paired results, rejected reasons, and accepted results. Calendar prices alone do not prove a booking is available. Both directions must be within 31 hours before a real deal alert is sent.

### Phase 2 — Compare maintained upstream against stable Fli

GitHub Actions → `Personal YYC–ATQ Flight Watch (health + diagnostics)` → **Run workflow**.

Select `task: health`, `fli_channel: upstream`. The scheduled run defaults to a pinned upstream revision `881aee5ff4321e81ea2157cb44be94ce6a21dc1b` (maintained after the published 0.9.0). This uses the GitHub source because PyPI's stable `flights==0.9.0` cannot provide newer fixes. The pinned revision is an experiment: it is **not yet proven** against this route. To compare, repeat health with `fli_channel: stable`. The `requirements.txt` file stays stable so downgrading takes one selection, not a code change.

Optional independent **cached historical discovery**, not a live offer source: set a `TRAVELPAYOUTS_TOKEN` GitHub Actions secret. The bot requests cached YYC/ATQ signals for the two detailed date pairs, saves them with verification `cached_unverified_no_durations`, and **never** sends a fare alert from this feed. Travelpayouts is a partner API and may return no data; joining it requires your own token/account. Real-time independent source and checkout verification remain future work if current free sources cannot deliver them.

### Phase 3 — Dates and coverage

The bot initializes all **216** departure/return pairs for Jan 25–31, 2027 and 60–90 nights in India, latest Apr 30. It cycles two duration-based calendar requests and two detailed round-trip date pairs per four-hour scheduled run. `COVERAGE` prints counts and fractions of total pairs covered by each method; it distinguishes attempted detailed searches from **nonempty results actually obtained**. Empty provider results are marked `provider_empty_unverified`, not genuine no-inventory. Date selection prioritizes never-tested pairs so one cheap pair cannot permanently starve the remainder.

**Limit:** two detailed date pairs every four hours means a complete first detailed pass can take ~18 days (216/2/6 runs per day), assuming no errors. Calendar lengths can cover all 31 stays in ~2.6 days but may return no quotes for some pairs. A complete exhaustive live 216-pair fresh scan every four hours is **not** achieved. Do not increase request rates until health, runtime and provider limits have been verified.

### Phase 4 — Validate and test alerts

Create private GitHub Actions repository secrets in **Settings → Secrets and variables → Actions → New repository secret**:

- `TELEGRAM_BOT_TOKEN` from your own Telegram bot.
- `TELEGRAM_CHAT_ID` for your Telegram chat.
- `TRAVELPAYOUTS_TOKEN` (optional; independent cached-data provider).

Choose `task: test-telegram` once from Run workflow; you should receive a clearly labeled test message. Never paste Telegram tokens into commits or a public discussion. Real Telegram alerts require a live paired fare at or under CAD $1,900, both directions at or under 31 hours, and deduplication. The CAD $1,600 target gets an additional target label. Fares above $1,900 are recorded for history if otherwise valid; this is **not checkout-price verification**, and a search link may not reproduce the exact quote. No auto-booking.

To inspect on Codespaces:

```bash
python -m unittest discover -s tests -v
python tracker.py status
# With the Fli dependency installed and network available:
python tracker.py health
```

Because the SQLite database contains your personal travel dates, prefer **private repository** access when possible. On a public repository, its committed database and previous commits are public, including historic contents even if you later delete the file.

## Development and persistence update

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for current acceptance evidence and
unresolved live-access blockers. Use Python 3.12 and an isolated virtualenv:

```sh
python3 -m venv /workspace/venvs/atq-flight-bot
. /workspace/venvs/atq-flight-bot/bin/activate
pip install -r requirements.txt
export FLIGHT_DB=/workspace/atq-flight-bot-local/fares.sqlite3
python -m unittest discover -s tests -v
python tracker.py scan --dry-run
python tracker.py status
# Only when provider access is permitted:
python tracker.py health
```

Development commands should set FLIGHT_DB to avoid modifying the historical seed
tracked in `state/fares.sqlite3`. The scheduled job now restores history from the
`flight-data` branch, seeds from the tracked database only on first use, and saves
using SQLite's backup API. It never rebases a SQLite database onto main. Keep
Actions contents-write permission and allow ordinary bot pushes to `flight-data`.
Do not run another independent writer against that branch: a racing push fails
visibly rather than overwriting history. A failed persistence step leaves a
14-day database artifact for recovery. Restore the latest known-good artifact
manually after investigating integrity/push failures; never silently reset history.
Artifacts have finite retention; the data branch is the durable source.

The four-hour schedule is unchanged. At two detailed pairs per run, the minimum
first pass is 18 days; reported percentages are cumulative, not freshness claims.
Calendar and detailed checks have separate coverage. Failed detailed attempts
count as attempted, not nonempty or valid. A parser/currency/identity failure makes
the scan fail even if other offers succeeded. Duration-only rejections can be a
healthy provider outcome. Empty results always remain unverified availability.

For Telegram, set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in GitHub Actions secrets,
then manually dispatch `task: test-telegram`. This sends a real message. Local
mock tests prove formatting/dedup/retry behavior, not delivery. Failed deliveries
are not deduplicated away. Successful duplicate itineraries alert again only on
a price drop of at least CAD 100. Search quotes never imply checkout confirmation.

Troubleshooting: CONNECT 403 in this cloud environment requires applying the
saved network-domain additions in environment settings. A Google HTTP block,
429, CAPTCHA or rate limit is a provider limitation; stop rather than bypass it.
A strict unknown-currency rejection requires inspecting the response/parser,
not assuming the requested currency was honored. Use `health` independently of
`scan`; inspect PROVIDER HEALTH, LIVE DIAGNOSTIC, COVERAGE, workflow summary,
and retained database before interpreting an empty result. The independent
Offline validation workflow tests both stable and pinned upstream without
credentials or flight requests.

### Provider research and live acceptance

See [the codebase comparison](research/PROVIDER_COMPARISON.md) for five alternative
implementations and their actual contract gaps. Bounded GitHub runner experiments
now return sanitized JSON on the `flight-provider-evidence` branch. These reports
are observations, not checkout proof or evidence that the full date grid is fresh.

Ordinary browser experiment 41578961275 decoded seven outbound options but was
rejected during selected-return expansion. Browser mode remains experimental;
it is not an automatic production fallback. Diagnostic provider workflows are
manual-only after that rejection. They stop on denial/consent and never solve
challenges. Stable and upstream HTTP comparisons also show intermittent empty
data. Reliable live round-trip retrieval has **not** been established.

An independent source requires authorized access with verified free live quota.
The repository has no configured Amadeus credentials or Travelpayouts token;
Amadeus sandbox would demonstrate integration only, not real fares. Do not enable
production billing or substitute demo/cache results as live prices. Telegram is
currently deferred. Current offline test count is 31 per provider version.

### Selected optional API candidate (credential required)

SerpApi's first-party [pricing](https://serpapi.com/pricing) currently lists a
Free $0/month plan with 250 searches/month. The prepared optional adapter refuses
paid/unknown plans and requires two remaining searches before a round-trip probe.
It reserves requests conservatively, caps local usage at 8/day and 240/month,
and never enrolls accounts or upgrades plans. This is **not yet enabled as the
production flight provider** and has not retrieved a live fare in this task.

To unblock its real test, create/use a **Free** account and add `SERPAPI_API_KEY`
in repository **Settings → Secrets and variables → Actions**. Never paste the
key into chat, code or logs; leave paid upgrades disabled. The runner checked
for an existing key and reported `credential_missing` without provider calls.

The agent can then run `scripts/serpapi_probe.py` in the runner and inspect its
sanitized evidence. A probe's candidate quotes are not a completed integration.
Before production use, validate real selected-return price/ticket semantics,
persist quota reservations with history, and verify repeated scans. The free
budget covers at most 120 paired searches/month, so full-grid rotation can take
about 54 days. Do not advertise all 216 combinations freshly checked every four
hours. Amadeus's production billing requirement and Kiwi's access denial are
recorded in [provider eligibility](research/PROVIDER_ELIGIBILITY.md).
