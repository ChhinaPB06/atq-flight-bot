Calgary's January 2027 UTC offset differed between the cloud and CI images.
The scanner and stored-fare audit now explicitly load pinned tzdata2026.6
(IANA2026f), so whole-journey duration validation uses the same current rules.
New quotes retain the rules version. A regression rejects an itinerary older
rules would admit as30h30 but current rules calculate as31h30.

Add a read-only54pair CSV/JSON export with explicit observation timestamps,
freshness, provider/status, CAD price and duration checks. Live run41654025980
completed the remaining16initial attempts:54/54attempted cumulatively,44with
usable quotes,5provider-empty/unverified and5validation-filtered. The degraded
run remained visibly failed, preserved all116prior observations and saved147;
all134active-pair APIobservations pass the current-rule audit. Best observed
CAD2074 Jan29/Apr21 is a search quote, not checkout-confirmed.

The manual native-alert pilot imports approved.eml exports into a separate
unverified/deduplicated table and can explicitly verify through the existing
Free-budget client. Its tests use synthetic email; a real Google alert template,
mailbox ingestion and all54native watches have not been demonstrated. Telegram
remains deferred. No paid source, new account permission or billing is enabled.

Validation:58tests per stable/upstream; remoteCI41656960169 passed; actionlint
and gitdiffcheck pass. Four-hour scheduling remains subject to Free limits:
after the initial pass, at most2pairs/day, approximately27days for a54pairrotation.
This does not meet fresh detailed54pairverification every4hours. Full readiness
is not claimed. Repository policy blocks Actions PR creation; this file is
prepared review text, not evidence that a PR exists.
