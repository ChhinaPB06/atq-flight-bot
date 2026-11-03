# Completely free flight monitoring: first-principles research

## Finding

The best-supported zero-new-subscription approach found is **native Google Flights
price watches → local alert ingestion → selective confirmation using the existing
Free API allowance**. It changes where monitoring occurs: the provider watches
its own data, and our program processes price-change notifications. It avoids
paying to poll every pair repeatedly. It is not a verified guarantee that all54
paired itineraries are freshly retrieved every4hours.

No account, inbox, alert subscription, new API key, paid plan, cloud instance or
message destination was accessed/created by this research. Current Free monitor
and its budgets remain active. No known provider block was retried or bypassed.

## First principles

1. We need externally observed fare/inventory state, actual dates/currency and
   both whole-journey times. A model or physical cost estimate is not that state.
2. The108calls/cycle count belongs to our two-stage API contract; it is **not a
   physical or mathematical minimum**. A complete authorized bulk feed, or a
   complete stream of changes, could convey the same information more cheaply.
3. We have not found a verified free bulk feed/complete change stream meeting
   all54datepairs, fresh4hcoverage and independent31hvalidation. Calendar data
   and native alerts provide less information/guarantees, so label them separately.
4. Most polling is unnecessary for the narrower practical goal “notify me when
   a qualifying cheap fare appears.” Event-based discovery can use far fewer
   confirmations, although provider notifications can miss/omit changes.

The correct distinction is fresh data versus free computation. Free software,
cloud credits or models cannot remove upstream quotas or access requirements.
This is not a proof that a free source can never exist; it is the limit of the
sources verified in this task.

## A. Native price alerts: credible free alternative

Official [Google Flights price-tracking help](https://support.google.com/travel/answer/6235879?hl=en)
was fetched200in source41595990032. It supports tracking specific dates, routes
and selected flights. It sends email when tracked prices change **significantly**.
“Any dates” watches a route's monthly minimum; it is not equivalent to our54
specific datepairs. No API subscription is required for this consumer feature.

Proposed pipeline:

1. Enable native date-specific watches for the permitted Jan27–31/80–90day pairs,
   or a supported subset plus a broader route watch. Provider/account capacity
   for54simultaneous watches has not been tested; no unlimited-watch claim.
2. Use a dedicated mailbox folder or approved exported messages. Standard Python
   MIME/HTML parsing and SQLite suffice; no paid model or Notion dependency needed.
   Do not access an inbox without authorization or fetch tracking/unsubscribe URLs.
3. Store each signal as **notification_reported_unverified**, with source, dates,
   explicit currency and message observation time. Reject ambiguous $symbols and
   unsupported dates. Preserve higher-priced signals as discovery history too.
4. Prioritize promising prices/large drops/preferred or stale pairs for Free API
   confirmation. Independently check complete journeys, actual CAD and dates,
   <=31h/direction and genuine paired-price semantics before a qualifying alert.
   One failed bounded search does not prove the emailed fare is nonexistent.
5. Deduplicate notifications and completed confirmations. The bot can process
   signals every4h; provider email cadence is its own, not a4hguarantee.

Budget: two-stage confirmation costs up to2calls/event. At local240/month cap,
up to120confirmations/month are possible before other usage. An initial full54
pass reserves108, leaving at most132calls/66confirmations that first month before
failures/other consumption. Reallocate routine polling budget to events rather
than adding unbounded extra calls. Excess signals stay unverified/queued; do not
claim every alert is confirmed. Manual normal-browser confirmation is another
no-API-cost option, requiring the user's time and normal permitted access.

Setup links: run `python scripts/native_alert_setup.py --output <file.csv>`.
Generated /workspace/native-flight-alert-setup.csv has54date links and false
setup/capacity flags. **No native watches have been created.** A search link is
not a guarantee it reproduces an exact quote; verify displayed dates/CAD before
turning on tracking. A real authorized/anonymized sample email is needed before
claiming a reliable parser against the user's actual locale/template.

## B. Repositories inspected for this angle

| Repo / inspected revision | What it demonstrates | What prevents blind adoption |
| --- | --- | --- |
| [fredrikfh/notion-flights](https://github.com/fredrikfh/notion-flights), efd447afdd881873bcf6576bc92144920862d16d | IMAP Google-alert parsing into structured records | Notion credentials, localized template logic; no license file established. No code copied. |
| [AKinoshita0915/flight-price-tracker](https://github.com/AKinoshita0915/flight-price-tracker), a8866d5f1c57aa36994189fa0b7245bc7174ead4 | MIT; Google-alert history extraction | Price regex matches several currencies but extraction drops currency identity; no validated full itinerary/date contract; Python3.14/heavy plotting dependencies unnecessary here. |
| [Alepazz/flight-monitor](https://github.com/Alepazz/flight-monitor), 858e4488c0fef4a84e212ab1c5655d6d35e8882c | Local LaunchAgent/cron orchestration and no-key UI client | Underlying fast-flights/Google source, not independent free inventory. It looks up returns separately; cannot assume chosen return matches an outbound round-trip price. README MIT declaration; no copied implementation. |

Earlier Fli,fast-flights,FlightScanner,Travelpayouts and Kiwi studies remain in
PROVIDER_COMPARISON.md. Several free repos merely wrap the same Google data source.
Changing wrappers does not create additional authorized quota or solve a refusal.
Known blocks are not a reason to rotate proxies, cloud IPs, accounts or trials.

## C. Free hosting/cloud: useful for execution, not fare access

- Existing owned computer + Python + cron/TaskScheduler: no additional cloud/API
  subscription. The device must be on; power/network costs and source permission
  still apply. This is not an assertion that a blocked scraper becomes permitted.
- [GitHub Actions](https://docs.github.com/en/billing/concepts/product-billing/github-actions):
  current official docs express included private-repo compute as a monetary
  allowance (GitHub Free:$12), not a universal fixed2000minutes. Stay within the
  actual account's included compute/storage with zero-spend settings; no billing
  settings were changed/verified here. Standard public-repo compute differs, but
  do not make personal travel data public to obtain free compute. Browser polling
  can use much more resource than processing email events.
- [Oracle AlwaysFree](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm):
  quotas apply; official docs say idle instances may be reclaimed. Capacity,
  enrollment requirements and production availability must be checked. No signup
  or fake utilization to avoid reclamation. It does not grant fare-data access.
- [Google Cloud free program](https://cloud.google.com/free/docs/free-cloud-features):
  official docs distinguish90daycredits/FreeTier/payment profile and paid billing
  upgrades. A trial is not perpetual zero-cost hosting. No enrollment/paid upgrade.

Existing included hosting is adequate for an event-driven prototype; adding
another cloud account is not necessary before data ingestion is demonstrated.

## D. Models, physics and open datasets

- Standard Python can compute actual duration for known schedules:
  arrivalUTC−departureUTC in each direction, using IANA airport timezones. This
  includes layovers and costs no model/API call. Existing validation already does
  conservative elapsed-time checks. Reuse computed duration only for identical
  operating-date/flight/time identities; a datepair alone is not an itinerary.
- Time-dependent shortest-path/connection filtering can prune impossible routes
  when trustworthy schedules are available. Great-circle distance/cruise-speed
  bounds cannot determine fares, seat buckets, taxes or actual availability.
  No fuel/distance model can certify a liveCAD1600booking price.
- Free [OpenFlights route/airport data](https://github.com/jpatokal/openflights/tree/master/data)
  was inspected via official repo files: route rows contain carrier/endpoints/
  equipment and airports contain coordinates/timezone, not fresh ticket prices.
  Static routes are not proof a future flight operates on a particular day.
- Historical datasets and forecasting/LLM models can rank candidate dates, not
  observe today's private fare/inventory state. Training a model or running an
  autonomous research loop does not manufacture fresh quotes. Optional local
  models may assist parsing; deterministic currency/date/identity checks remain.
- Decomposing into5outbounddates+14returndates reduces one-way research to19dates,
  but adding their prices creates **separate tickets**, not a genuine round-trip
  fare. It may miss round-trip discounts and still needs live source access.
  Never substitute that sum for the user's primary round-trip quote.

## Decision and limits

Recommended free next implementation: native-specific-date alerts plus an
approved narrow email input and the existing Free API verifier. Prepare54links,
validate one actual alert template, preserve unverified signal confidence, and
allocate the same quota to promising events. No new paid model, MCP platform,
Notion service or cloud account is required for that design.

This is a credible zero-new-subscription architecture, **not a delivered inbox
integration** and not proof of all54fresh detailed quotes every4hours. Required
one-time user actions are native-watch setup and approval of a narrow email
source; no passwords/keys in chat. The rigorous full-frequency goal still lacks
a verified free upstream source. Keep that limitation explicit rather than
silently relaxing the acceptance gate.

## Evidence limitations

Official Google tracking, GitHub billing, Oracle and Google Cloud docs fetched200
in source41595990032. Skyscanner help/API, Duffel pricing and OpenFlights website
returned403; no alternate-IP retries. Travelpayouts and route-optimizer guessed
URLs returned404; no claims inferred from those pages. OpenFlights official
GitHub data was publicly available. Repository inspection is static evidence;
no new repo's live fare retrieval or private-mail integration was tested.
