# Lower-cost whole-grid monitoring options

## Workload and scope

54eligiblepairs,6runs/day.30days:9720completepairchecks.31days:10044.
Two-stage APIs:19440/20088requests respectively, before retries/extra expansions.
One-call complete-pair APIs:9720/10044requests respectively. A quote requires
both actual journeys, CAD, dates, economy and <=31h including layovers; neither
an outbound-only total nor a calendar price proves those requirements.

Prices below are publisher-listed dollar subscription prices, not CAD airfare.
Billing currency/taxes, exact live listing and endpoint metering must be confirmed
before any paid enrollment. No account, subscription or billing change was made.

## Best low-cost candidate: FlightPowers (not live-validated here)

Primary sources: [pricing](https://flightpowers.com/pricing),
[docs](https://flightpowers.com/docs),
[publisher Python SDK](https://github.com/mtnrabi/google-flights-api-python),
SDKrevision9787d049faef2fead3e4e97a95ecb8b82ee2050e.
Pricing/docs retrieved by research source41592494316. Publisher/RapidAPI identity
matches mtnrabi; direct RapidAPI pricing page returned403, so live billing terms
must be rechecked in the actual account before enrollment.

Publisher explicitly advertises both legs/one total/one booking link in one
request (no second departure-token call). SDK has departure_flight_duration,
return_flight_duration, airports/dates and total_price fields; currency is an input
parameter. These are contract claims, not proof of correct YYC–ATQ CAD responses.
Model fields are optional and separate-ticket semantics remain to be verified.

| Flight plan | Published quota | Monthly price | Overage |
| --- | --- | --- | --- |
| BASIC | 10requests | Free | Hard cap |
| PRO | 2500requests | $10 | $0.003/request |
| ULTRA | 10000requests | $25 | $0.002/request |
| MEGA | 25000requests | $50 | $0.0015/request |

ULTRA supports the9720baselinechecks in a30daymonth.31days requires44overagecalls:
$25+44×$0.002=$25.088(~$25.09), before retries/taxes. Do not claim10000covers a
31daymonth or assume failed calls are free. With10044checks plus5%extra requests
(ceil502.2=503), estimate$25+(10547-10000)×$0.002=$26.094. A proposed$30usage budget
could cap12500calls only after actual billing/metering is verified; it is not an
authorized spend. MEGA provides large headroom for$50if avoiding routine overages
is preferred. Do not buy multiple Free accounts or stack subscriptions to evade
limits. PRO alone cannot supply full-frequency coverage.

Recommended validation first: use the10-callFree/hard-cap tier, never paid auto-
upgrade. Verify YYC–ATQ complete pairing, CAD response interpretation, both journey
elapsed times, actual dates/cabin, self-transfer/separate-ticket labeling, live
freshness, failures and whether exactly1request is metered per pair. Compare
against known actual itinerary/price data, then repeat. No provider key for this
service is configured/used in this research. No reliability claim or provider
switch is justified by advertising alone.

## Documented fallback: SearchApi

Primary [pricing](https://www.searchapi.io/pricing) and
[GoogleFlights API](https://www.searchapi.io/docs/google-flights-api), sources
41591948276/41592494316.2-stage outbound/selected-return flow is documented.

- $40/month:10000searches. Insufficient for all54detailedpairs every4hours.
- $100/month:35000searches. Advertised capacity covers20088two-stagecalls and
  normal headroom, assuming standard per-search billing for this endpoint.
- 100free requests advertised/no card, not verified as a recurring monthly tier.

This is about64%less subscription cost than SerpApi's$275plan below, but actual
YYC–ATQ handling, CAD, pair prices and endpoint metering still need a keyed trial.
Do not assume a subscription-price comparison establishes live reliability.

## Lowest-request screening alternative (different guarantee)

Primary [SearchApi Calendar API](https://www.searchapi.io/docs/google-flights-calendar-api)
(source41592494316) permits up to200outbound/return combinations per request.
Jan27–31×Apr17–30=5×14=70combinations, of which54meet80–90days/Apr30cutoff.
One calendar request can screen that rectangle, filtered locally to the54pairs.
Six screens/day need180requests/30days or186/31days, rather than19440/20088.

Calendar responses are date/price discovery. They do not provide the full selected
outbound/return itineraries required for independent31hvalidation. Do not relabel
all54as detailed/fresh verified fares. A design with1calendar+3detailedpairs per
run needs7requests/run,1302in31days; with an initial108requestdetailedpass,
1410requests fit the advertised$40/10000plan. Only3pairs/run have the detailed
guarantee. Even during cheap-price spikes, a hard budget must limit details.
No claim that Google's calendar quotes are checkout totals or exhaustive inventory.

## Current known-working source: SerpApi

Primary [pricing](https://serpapi.com/pricing) and
[flight API](https://serpapi.com/google-flights-api), source41591948276.

- Free250/month: usable for limited rotation, not full-frequency coverage.
- $150/15000: insufficient for the full two-stage workload.
- $275/30000: advertised capacity covers20088plus headroom.
- We have actual live YYC–ATQ/persistence evidence only for this provider so far.

## Other candidates and rejected cost shortcuts

- [HasData official MCP repository](https://github.com/HasData/google-flights-mcp),
  revisionb058b2abca6ecce37c49279353d681af9e4f0fed, documents15credits/call and
  2calls/roundtrip. Full31dayworkload needs301320credits. Free1000credits/month
  gives~33completepairs, not1000pairsearches. Publisher README says entry$59for
  200000credits, which is insufficient; current pricing page returned403, so
  next-tier pricing is unverified. Do not compare generic credits as flights.
- Scrapingdog pricing lists$40/200000credits, but a supported flight endpoint and
  flight-specific multiplier were not established. Cannot call it a fitting
  cheaper provider based on generic scraping credits.
- FlightAPI.io docs are available, but the queried pricing route returned404;
  actual applicable subscription/metering was not established. Do not guess.
- Travelpayouts cached data is not an independently duration-verified live offer.
- Amadeus production requires billing enrollment and may autocharge over quota;
  no enrollment under the current no-spending authorization.
- Previously tested direct Fli/browser paths were intermittent/rejected; no
  repeated retries, CAPTCHA solving or proxy workarounds for blocked sources.

## Decision

Best next no-spend experiment: FlightPowers Free10calls, if the user supplies an
authorized Free key. If it passes live validation, ULTRA is the lowest priced
credible full-workload candidate found (~$25–$30/month subject to metering/retries;
MEGA$50forheadroom). SearchApi$100is the better-documented fallback. Calendar-led
screening$40is useful only if reduced detailed verification is acceptable.
No verified zero-cost source found for all54detailedpairs every4hours. Keep current
Free monitor active until a replacement is tested and any paid spend explicitly
authorized. This research did not use flight credits, obtain new keys or change
production provider/quota settings.
