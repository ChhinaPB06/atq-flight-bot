# Ways to reduce flight-search cost

## Exact goal versus cheaper approximations

54datepairs,6executions/day,31days. Current2-stage fresh date-pair discovery needs
20088flightAPIcalls. This already expands only1validoutbound/pair; it is not an
exhaustive expansion of every airline itinerary. Do not claim a further saving
from reducing an expansion count we never used.

| Approach | Calls/31days | Reduction | What is freshly checked |
| --- | ---: | ---: | --- |
| Current2-stage full54eachrun | 20088 | baseline | Each datepair, bounded outbound choice |
| Validated1-call complete-pair provider | 10044 | 50% | Each datepair, if contract/live data pass |
| Calendarall54+3detailedpairs eachrun | 1302 | 93.5% | All calendar prices; only3pairs' journeys |
| Daily full54+calendar/3details other5runs | 4433 | 77.9% | All journeys once/day, selective checks between |
| Refresh fixed known itineraries | ~10044 | potentially50% | Selected flights, not new cheaper alternatives |

Numbers exclude retries, use1call/calendar screen and2calls/detail, and assume
chosen provider bills1search/endpoint call. They are request counts, not a promise
of provider data quality or a subscription charge. Reproduce with
`python scripts/search_costs.py --days 31` (also supports30days).

## 1. Batch calendar screening

Official [SearchApi Calendar documentation](https://www.searchapi.io/docs/google-flights-calendar-api)
permits200datecombinations per request. Our date rectangleJan27–31×Apr17–30 is70,
so1request can cover it; discard16out-of-scope pairs locally, leaving54.
Screening every4h needs186calls/month, not20088. Then detail-check newly cheap,
price-dropped, preferred and stale datepairs, within a hardK/budget per cycle.
A watch buffer aboveCAD1900 can catch approaching deals. Calendar prices above
the threshold still belong in discovery history, not as duration-verified fares.

Crucial limitation: the calendar does not supply the complete paired journeys
needed to independently enforce31h/direction. An unchanged or high calendar
estimate cannot prove there is no qualifying cheaper fare. Include fair forced
rotation for all pairs and a periodic full detail pass; label unsupported,
missing, stale and unverified records honestly. Never promote all54to fresh live
verification just because their calendar prices were refreshed.

The advertised SearchApi$40/10000plan fits1302calls and4433calls scenarios, pending
keyed live trial and endpoint-meter verification. Its100freerequest offer is not
verified as a recurring allowance. The current SerpApi key does not authorize
SearchApi, and no undocumented SerpApi bulk-date feature is assumed.

## 2. Reduce complete pairs to1call

FlightPowers publisher advertises both directions and total fare in1request.
This retains the full54-per4h frequency if actual CAD/date/cabin/elapsed-time/
ticket-type data pass. See COST_OPTIONS.md: its$25/10000plan fits30days;31days has
44extra calls, advertised$0.002each, about$25.09before retries/tax. Free10hardcap
calls can validate first. No key/account/paid enrollment was obtained here.
It is the lowest-price candidate found for retaining the exact detailed frequency,
not an independently proven replacement or a zero-cost way to run10044calls.

## 3. Reprice known exact flights

Official [SerpApi flight API](https://serpapi.com/google-flights-api) documents
selected_flights_json: explicit outbound and return segments pin an itinerary.
This may avoid rediscovering an outbound every refresh and is a useful next
1-call experiment using the existing source. Response pricing, real availability,
updated timings and ticket semantics still need a live trial before activation.
Do not call a refreshed known fare a fresh market search; it misses new cheaper
routes and may lose a fare when that particular flight changes. Pair this with
periodic discovery rather than replacing all discovery indefinitely.

## 4. Cache correctly; no artificial freshness

SerpApi docs say exact same query/allparams can use a free cache for1hour.
That helps duplicate attempts/restarts within1hour. It does not make4hour
refreshes free. Do not relabel retained old observations as newly verified prices.
Do not reuse one return date's price for another date, infer CAD from a symbol,
combine separately quoted one-way tickets as a single booking, manipulate tokens,
rotate identities or evade rate limits to save credits.

## 5. Implemented now: reserve only the requests that can be made

Client still reserves2before searching and preserves reservations after ambiguous
failures. If a successful outbound response yields no selectable outbound, the
return request is provably never made. The local ledger now releases exactly1
unused reserved search in that case. This is local capacity accounting, not a
provider-billing refund and not a reduction in the required full-grid workload.
Regression tests verify no return request occurs and ambiguous return failures
retain2. Account Free/$0, remaining allowance, rollinghour/day/month caps remain.

## Recommended decision

To retain every54pair detailed check every4hours, first trial the1-call provider;
no paid enrollment without explicit authorization. For cheaper broad screening,
use calendar+selective detailed checks and clearly accept the reduced detail
freshness guarantee. With absolutely$0and current keys, keep limited rotation;
no verified method supplies all54fresh detailed checks every4hours for free.
The implemented reservation fix helps current Free usage without weakening
validation, changing providers or increasing any budget.

## Evidence

First-party docs fetched in source41593393737; pricing/contracts and SDK revisions
inCOST_OPTIONS.md. Research consumed no liveflight credits. No replacement source,
repricing path, paid plan or calendar-only acceptance rule was enabled.47offline
tests pass against each installedFli version. The larger choices are documented
experiments, not claims of delivered live functionality.
