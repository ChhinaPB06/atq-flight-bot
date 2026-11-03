# Native price-alert pilot

## Implemented

- `signals/native_email.py` parses an explicitly supplied `.eml` export locally.
  It reads the preferred message body, ignores attachments/script/style content,
  and does not fetch links, tracking pixels, mailboxes or other network resources.
- Strict pilot requires an explicit Calgary→Amritsar route, exactly one active
  datepair with fullISOyears, one explicit CAD/CA$/C$amount, and a timezone-bearing
  message Date. Ambiguous currencies, multiple prices/dates, unsupported layouts
  and out-of-scope pairs fail closed. No inferred current year or `$` currency.
- Reported prices use integer cents. Import stores only extracted travel facts,
  a deduplication fingerprint and timestamps, never raw email/sender/recipient.
  Source authentication remains unverified; an export is not proof of Google origin.
- Signals live in a separate native_events table with unverified status. Import
  never creates a live fare observation or advances detailed coverage.
- Explicit verification calls the existing Free-only SerpApi client, shares the
  persisted budget, stores actual fares and diagnostics, and compares actual
  price with the alert threshold. It never substitutes an emailed price for a
  returned fare and never sends Telegram. Completed events are not re-queried;
  quota/credential failures remain explicit. One verification in progress is locked.
- `.eml`/`.msg` exports are ignored by Git. Keep private files outside the checkout.

## Evidence and limitations

54local tests pass under both installedFli versions. Native tests are **synthetic**:
CAD cents, HTML/script exclusion, ignored attachment, ambiguous field rejection,
deduplication, no live observation on import, actual-vs-reported price, completed
verification dedup and quota deferral. CLI smoke import twice returned the same
id and unverified status. No private inbox, Google watch or real email was used;
no API call or notification was made for these tests.

Actual Google email layouts may omit years, contain old and new prices, use
localized month names, or encode dates only in links. Those are unsupported until
we inspect a real approved/anonymized fixture and implement/test that contract.
The strict pilot must reject them rather than guess. This is not a claim of a
live end-to-end native-alert integration or of all54fresh results every4hours.

## One-time user action to unblock the real pilot

1. In your signed-in browser, open a single test search:
   https://www.google.com/travel/flights?q=Flights+from+Calgary+to+Amritsar+departing+2027-01-27+returning+2027-04-20&curr=CAD
2. Verify the UI shows YYC–ATQ roundtrip,1adult/economy,CAD,Jan27/Apr20,2027.
   Enable **Track prices** for those specific dates. This session has no signed-in
   browser/mail connector and cannot enable it for you. Do not share a password.
3. When an alert is available, export it as `.eml` (“Download message/Show original”
   in your mail app). Supply one approved/anonymized sample, retaining visible
   trip dates/year, price/currency, subject and message Date/timezone. Remove your
   name, recipient/address and private tracking identifiers. Never include tokens
   or passwords. We need the actual layout before claiming reliable parsing.
4. Parse that sample and inspect extracted unverified facts before authorizing
   its one bounded live verification. The existing API key is in GitHub Secrets;
   do not copy its value into chat or email exports. Arrange a secure execution
   binding when the real fixture is ready; this pilot does not extract GitHub keys.

The complete54linklist is `/workspace/native-flight-alert-setup.csv`, generated
by scripts/native_alert_setup.py. All enablement/capacity flags remainfalse.

## Local commands

```sh
# Offline import: no mailbox access or provider call.
python scripts/native_alert_pilot.py --db /path/outside-checkout/pilot.sqlite3 import /path/approved-alert.eml

# Explicit network verification, only with securely configured existing Free key.
# Real use must share the same restored/persisted fare/budget DB as routine scans.
python scripts/native_alert_pilot.py --db /path/to/restored/fares.sqlite3 verify EVENT_ID
```

Do not create a separate real quota ledger to bypass the routine budget. The
standalone pilot is not yet wired into the scheduled job or any mailbox. It
reuses tracker DB schema and all-table persistence when using the production DB.
A process killed while verifying may require manual recovery of the event lock
after confirming no verification is still in flight; no automatic retry loop.

No Google/mail account settings or paid service changed. The running Free monitor
continues its current scan cadence, scope, budget and deferred-Telegram behavior.
