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
