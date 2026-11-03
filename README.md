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
