# Provider/codebase comparison

Source inspection, not live endorsement. No candidate has yet demonstrated a new
YYC–ATQ fare in this task. Inspected primary sources and exact revisions:

| Candidate | Fit and evidence | Decision |
| --- | --- | --- |
| [Fli](https://github.com/punitarani/fli), stable 0.9.0 and upstream 881aee5ff4321e81ea2157cb44be94ce6a21dc1b | Existing one-adult/CAD/date filters, complete selected outbound/return pairing, per-journey duration, typed errors. Stable RPC and upstream page transport differ. Current live access blocked here. MIT. | Retain provisionally; trace fetch stages, test in intended GitHub runner. |
| [fast-flights](https://github.com/AWeirdDev/flights), 4261437c506b228d20969910178a19e6d1bd2592 | MIT; currency query and round-trip inputs; parser reads both best/other groups. model.py exposes one flights list and per-segment durations, no returned currency or selected-return pairing. fetcher.py returns one parsed page. Same Google dependency, not independent inventory. | Useful parser reference, insufficient drop-in replacement for both-direction validation. No paid proxy integrations selected. |
| [FlightScanner](https://github.com/klebermc/FlightScanner), ad0da9f49333c479bd222519c946b07ad84d4f9a | MIT; useful day/stay enumeration, HTML-to-Playwright response capture pattern. README explicitly says outbound-only; src/flight_scanner.py sums flying minutes, excluding layovers, and labels currency from request. | Do not adopt its fare acceptance logic. Standard Playwright observation may be worth a bounded experiment if ordinary page data is missing; not for evading blocks. |
| [flightsearch](https://github.com/ostrvcxztd/flightsearch), 4eda41e2595883c9556994dd93fb8d2836897816 | MIT; stdlib/cache/date range architecture; app.py uses Travelpayouts prices_for_dates and defaults to generated demo data without token. Cached data is not a live offer; advertised currency list omits CAD. | Secondary discovery only; never primary live/alert source. |
| [FlightSearcher](https://github.com/FrancescoBellingeri/FlightSearcher), 5da7e2801dd01020148c0e42346f1b307cc3387c | Independent Kiwi browser/GraphQL source. format_flight_data selects sectorSegments[0] in each direction and loses full-journey duration and currency. README asserts proprietary ownership; no permissive license established. | No copied implementation or deployment. Synthetic source-function check: a 2100-minute multisegment direction reports only 60 minutes. Cannot enforce our limit as written. |
| [Amadeus Python SDK](https://github.com/amadeus4dev/amadeus-python), 0bc7089cb2e49b5b662ee890a5fe611f59ad4332 | MIT official SDK; FlightOffersSearch calls /v2/shopping/flight-offers. README requires account/client ID/secret, defaults to test; production is described as pay-as-you-go. | Best official independent API candidate to investigate with credentials and verified free quota/coverage, not enabled or represented as free live data today. Test data cannot satisfy live gate. |

## Selected approach

Keep the lightweight existing Python/SQLite/Actions monitor, isolate provider
experiments, and diagnose Fli's actual missing boundary before replacing it.
Research does not support a currently verified, credential-free, independent
replacement that meets every requirement. Do not confuse software license cost
with provider access cost or imply a wrapper creates independent inventory.

Add trace evidence at _fetch_flights in both pinned versions: initial outbound
rows versus selected-return rows, classified errors, and empty stage. Tests run
actual Fli expansion logic with controlled decoded responses, not HTTP. There
are now 26 offline tests per provider version. New private-API tracing is a
maintenance risk, covered by the two-version tests and explicit pin.

GitHub Actions is an already authorized deployment target. A bounded diagnostic
workflow on the development branch tests one pair/version (top_n=1, 120 seconds,
10-second spacing) and publishes sanitized results to flight-provider-evidence.
That is a normal CI execution experiment, not a proxy bypass. It sends no
Telegram messages, writes no production fare history and performs no booking.
Push access allows reading that evidence branch even while API log access is
unavailable. CI execution and source response quality remain to be observed.

No additional paid API, agent SDK runtime, browser dependency or proxy service
was installed in the application. See FRAMEWORK_REVIEW.md for agent frameworks.
