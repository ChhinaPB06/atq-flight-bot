# Independent-provider eligibility decision

## Amadeus: not eligible for autonomous production enrollment

Primary source: official [amadeus4dev/developer-guides](https://github.com/amadeus4dev/developer-guides),
revision `6ecaad720eb122f765a2f205bf948a2a300c9111`.

- `docs/API-Keys/moving-to-production.md`, steps 3–6: personal/billing details,
  payment method and signed terms are required for production keys.
- Same document: over-free-threshold transactions are billed automatically.
- `docs/faq.md`, “Is the data returned in the Self-Service test environment
  accurate?”: test uses limited data collections; complete/live data is production.
- Free test quota is useful for an adapter test, not the live monitoring acceptance
  gate. Existing GitHub credential-presence checks found no account keys.

Decision: do not create an account, enable production billing or integrate this
as a purported free production solution under current authorization. This is a
confirmed eligibility problem, not an agent-framework limitation. An account
with a separately authorized, enforceable zero-spend arrangement could change
the decision, but no such arrangement has been verified.

## Kiwi: bounded public observation, pending

The ordinary public website is independent of the previously tested Google
transport. One normally rendered search is an admissible experiment with no
account creation, spending or automated booking. It is not a verified stable
API entitlement and is not a deployment decision. Stop on access denial or
challenge. Do not add stealth, token replay, proxy rotation or repeated retries.

Only independently authored observation code is used. The proprietary comparison
repository's implementation was not copied. Whitelist public fare/itinerary
fields; exclude booking/session tokens. Before any acceptance or alerts, require
returned currency, full endpoints/dates, complete directional duration including
layovers, and an honest ticket-type label (a Kiwi itinerary may involve separate
tickets/self-transfers). A requested CAD parameter alone is insufficient proof.

A schema-only response, absence of data or challenge is not a successful fare.
Do not persist speculative prices as verified/live fares or send notifications.

## SerpApi: selected optional API candidate

First-party pages retrieved successfully by source run 41582497237:
[pricing](https://serpapi.com/pricing) lists **Free, $0/month, 250 searches/month**;
[Google Flights API](https://serpapi.com/google-flights-api) documents `currency`
as returned-price currency and the second `departure_token` request for returns.
SearchApi's pricing page advertises 100 free requests/no card, but recurring
allowance was not established, so it is not preferred over the explicit recurring
SerpApi Free plan. No account has been created and no subscription upgraded.

Implemented optional providers/serpapi.py and a one-shot readiness probe. It
requires existing SERPAPI_API_KEY, checks account.json for plan_name exactly Free
and at least two searches left, reserves two searches atomically, and refuses
other/unknown plans. Local caps are 240 searches/month and 8/day. Failures do not
refund reservations, so ambiguous counted calls cannot exceed the local budget.

Before production integration, keep the quota table in the same persisted DB as
fare history; the current one-shot diagnostic's temporary DB is not a production
quota implementation. A durable 240/month budget permits at most 120 paired
searches/month (two API calls/pair), so a first 216-pair pass takes at least ~54
days at four pairs/day. Six scheduled triggers/day must include explicit quota
or no-live-search outcomes; do not promise fresh 216-pair coverage every four
hours. Existing account usage and other applications can reduce available quota.

The adapter is **not enabled in production**. Synthetic contract tests verify
returned CAD, actual route/date/cabin, whole-journey duration, selected-return
price instead of summing tickets, and rejection of explicit separate tickets.
Real price/ticket semantics and repeatability still require live response review.
Outputs are deliberately labeled candidate quotes, never completion or checkout
verification. No key, tokens or authenticated URLs are written to evidence.

Concrete remaining prerequisite: a Free-plan key in GitHub Actions secret
SERPAPI_API_KEY. Use the provider's Free signup and leave paid upgrades disabled.
No agent can obtain that personal account credential from the repository when
it is absent. A missing key is reported without making any provider request.
