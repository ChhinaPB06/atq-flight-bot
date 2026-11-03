# Flight bot status and decision log

## Six-specialist integration checkpoint

User-authorized provider, coverage, native-email, persistence, scanner and
independent-acceptance specialists completed their assigned reviews. Coordinator
integrated fixes for disconnected/invalid journeys, subminute duration overflow,
provider failure classification, fair rotation after errors, stale current-price
reporting, ambiguous email fields, and corrupt/missing restore safety. Saving is
blocked after failed restore; backups are validated and atomically replaced.
CI live evidence now requires a dedicated scanner step plus actual searched dates.

88tests pass in both local dependency environments; actionlint/diffcheck pass.
Real immutable snapshot remains147observations,54completedpairchecks,44usable
pairs,5empty,5filtered and112reservedsearches. Current-rule audit134quotes and
independent268normalized-journey replay pass; replay is not fresh provider data.
Actual-history atomic backup preserves allcounts and integrityok. Specialists
made no provider/inbox calls and spent no flight quota. Integrated development
CI41670104760, mainCI41670336088 and production41670336017 passed. Main was
normally fast-forwarded c58a69e→8f87ab3. The first integration commit omitted
tracker.py; its follow-up included it before the complete candidate passed CI
and was deployed. See research/INDEPENDENT_ACCEPTANCE.md.

Post-deployment history comparison is exact:147observations unchanged,112search
reservations,54checks and lastAPIcheck14:34:29UTC. At16:04:26UTC the new scanner
persisted scan_idle with an explicit no-provider-request reason; that successful
workflow did not search all54again. Refreshed16:05UTC audit has23pairs quoted
within4hours, illustrating why cumulative coverage and freshness stay separate.

Genuine remaining gates: approved real native email and authorized ingestion,
unverified54Googlewatches, Free allowance insufficient for full54pair4hrefresh,
deferredTelegram and account policy preventing ActionsPRcreation. Today's112
reservedcalls exceed the steady4/daycap; no extra live validation is authorized
by the current local budget. Do not bypass it with another agent or quota DB.

## Current checkpoint — all 54 attempted; native integration remains incomplete

Run41654025980 completed the initial attempt pass:54/54datepairs,44with usable
fares,5provider-empty/unverified,5with returned fares rejected by validation.
No unchecked pairs remain. The batch correctly reported degraded status and
persisted progress. Observations116→147; every prior observation is preserved;
SQLite integrityok;112reserved searches total. Per-pair CSV/audit are generated
with scripts/coverage_report.py, which performs no network request or DB mutation.
25pairs had a quote within4hours at14:37UTC; cumulative attempts are not freshness.

Remote58test validation passed in41656960169 after a reproduced timezone portability
defect: host Calgary January2027offset differed between cloud/Ubuntu images.
Scanner/audit now explicitly use tzdata2026.6/IANA2026f. All134active-pair stored
quotes pass the current-rule audit, so best remainsCAD2074 Jan29/Apr21,
1810/1702minutes, observed06:31:27UTC. Not checkout-confirmed; no<=1900quote.
58local tests pass per Fli version, including a case that older rules would
wrongly admit as<=31hours. Remote stable/upstream CI passed with the corrected rules.

Native Google email ingestion remains untested against a real exported alert;
no inbox integration or54enabled watches has been demonstrated. Telegram is
deferred. Free quota cannot support fresh detailed54pairchecks every4hours.
No real PR exists because repository Actions PR creation is disabled.
The complete project therefore is not fully ready or acceptance-complete.

Deployment:normal fast-forward main9d0649b→c58a69e applied the validated timezone
fix and audit tooling. Production workflow41657335604 and mainCI41657334969 both
passed; developmentCI41657287852 also passed. No force push, account setting
change or alert enablement occurred. A green post-deployment run does not mean
all54pairs were searched again; the already completed first pass and normal
rotation/free limits still govern which queries can run. Initial live batch
41654025980 remains correctly degraded for its unusable responses.

## Acceptance status

Engineering work is **in progress, externally blocked**, not complete. No new live
YYC–ATQ fare was retrieved in this environment. No checkout verification occurred.
The previously reported Actions runs are user-supplied evidence, not independently
re-inspected logs. Telegram delivery and remote CI have not been demonstrated.

## Decisions and evidence (2026-11-02, America/Regina)

- Preserved the 216-pair grid, CAD thresholds, one adult/economy, 31-hour direction
  limits, and records above the alert threshold. No booking or payment code.
- Inspected stable `flights==0.9.0` and upstream
  `881aee5ff4321e81ea2157cb44be94ce6a21dc1b`. Stable uses the RPC endpoint;
  pinned upstream fetches the Google search page. Both expand selected outbounds
  into return searches. Upstream CLI documents outbound.price as full RT price;
  do not sum two segment prices. Healthy one-way calls do not establish RT health.
- Added production-boundary route/date/currency validation. Missing currency is
  rejected, not assumed CAD. Synthetic legacy parser tests are not live evidence.
- Stop after unhealthy provider probes, rather than continuing expensive scans.
  Provider library retries remain bounded; no outer retry amplification was added.
  HTTP rate limits/blocking, parsing errors, empty results and duration rejections
  remain distinct. Failed attempts update rotation and diagnostic coverage.
- Persist on an independent `flight-data` branch using SQLite backup/integrity check
  and ordinary fast-forward-only push. No pull/rebase of binary databases on main.
  Keep a 14-day artifact recovery copy. Test proves two successive restores/saves
  and rejects a stale writer. No remote persistence run has yet been verified.
- Added independent offline CI matrix for stable and upstream. Local 24 tests pass
  under both dependencies. Stable pip check and adapter import pass.
- Stable live three-route health failed with connection errors. Pinned upstream
  exact Jan 25 / Apr 16 RT with top_n=1 failed before data retrieval: CONNECT 403.
  Direct Google request also returned proxy CONNECT 403. This is an environment
  egress restriction, not evidence of missing flights or a proven parser defect.
- GitHub Actions log read via `gh api` returned Forbidden. HTTPS Git read works.
  No tokens were requested or extracted. Network draft adds www.google.com,
  api.github.com, api.telegram.org and api.travelpayouts.com; runtime remains blocked
  until settings are applied. No credential values were saved.
- No Telegram/Travelpayouts bindings were present. Requested Telegram credentials
  once, through secure settings. Notification delivery is tested with mocks only.
- Independent option evaluated: existing Travelpayouts cached API is not a live
  duration-validated source; it cannot satisfy the RT acceptance gate. No other
  credential-free authorized independent live source was verified. Do not invent
  fares, add paid APIs, or combine unrelated one-ways into a round-trip quote.
  Separate-ticket fallback is deferred pending actual validated provider data.

## Next actions once access is available

1. Reinspect runs 41573652801, 41574283529, 41574548188 through GitHub API.
2. Re-run exact Jan 25 / Apr 16 and preferred Jan 27 / Apr 15 under both isolated
   environments, with modest top_n and pauses. Inspect initial versus selected
   return payloads if empties persist. Save sanitized reproducible response fixtures
   before changing parsing or pairing. Do not bypass CAPTCHAs or provider denials.
3. Validate real returned CAD currency, dates, endpoints, durations and RT price;
   verify a repeated scan preserves observation history on flight-data.
4. Run Telegram test once using Actions secrets; never copy values into chat.
5. Observe matrix CI and an actual scan workflow; reconcile acceptance evidence.
6. Merge only after review. This branch does not change the scheduled main job
   until merged. Do not describe the empty-return root cause as repaired yet.

## Delivery checkpoint

- Pushed `fix/roundtrip-provider-persistence`, implementation commit `2dd05bb`.
- GitHub suggested its pull-request creation URL, but `gh pr create` failed:
  POST api.github.com/graphql Forbidden. **No PR was created.** Prepared review
  text is in PR_DESCRIPTION.md. `gh run list` also failed with Forbidden, so remote
  CI status is unknown. HTTPS Git push works; do not infer API readiness from it.
- Current runtime policy was rechecked after draft save: allowed_hosts remains
  empty. Draft persistence is confirmed; runtime application/publication is not.
- Final local checks: 24 tests pass in each provider environment, git diff --check
  passes, no modifications to tracked fare history.

## Agent workflow update

Added AGENTS.md with a bounded research/experiment/evaluate loop, explicit live
acceptance gates, persistent experiment records and tool-selection rules.
Research and source revisions are in research/FRAMEWORK_REVIEW.md; next experiment
and its prerequisites are in research/EXPERIMENTS.md. Telegram is deferred at the
user's request. No external agent runtime was installed and no claim of improved
live retrieval follows from the configuration change alone.

## Alternative codebase research and live execution path

Reviewed five alternative codebases at pinned revisions; findings are in
research/PROVIDER_COMPARISON.md. None is a verified drop-in solution for all
constraints. Added outbound/selected-return fetch-stage tracing and regression
checks against real Fli expansion logic; 26 offline tests pass per version.
Added a bounded GitHub runner experiment that can return sanitized JSON through
a dedicated evidence branch; this is pending execution, not proof of live fares.
Telegram remains deferred. Continue from E005 in research/EXPERIMENTS.md.

## Current live evidence (supersedes earlier access-only blocker)

GitHub HTML run pages and Git-hosted evidence provide a working observation path
although this machine's API access remains denied. Actual comparison source run
41578099055 returned 8 stable initial outbounds and 3 pairs, but new validation
rejected them due to an airport-enum normalization defect (.value contains the
full airport name; .name is the IATA code). That defect is now fixed and tested
with real Fli model instances. Original evidence did not retain enough identity
fields to retrospectively declare those fares validated.

Retest 41578488968 returned zero initial outbounds from both stable and upstream;
no usable validated live quote yet. A standard Playwright rendered-page experiment
is now testing the client-side-data hypothesis. First browser attempt failed in
setup, not at the provider. Supported Ubuntu 24.04 retry is run 41578961275.
Offline CI 41578961308 passed; 29 tests now pass locally under each Fli version,
including guards that stop browser experiments on HTTP denial or consent pages.

Draft PR automation run 41578624276 failed; no PR exists. The reason is not
established by its generic HTML annotation, and account settings were not changed.
The scheduled main deployment is unchanged. Do not claim project completion.

## Latest checkpoint: actual browser trial and external blockers

- Browser source run 41578961275: 7 decoded outbound options, then explicit
  SearchRejectedError at selected-return expansion. No usable complete fare.
- Real-model enum normalization fix remains tested; source/provider reliability
  is unresolved. The best-fit architecture is retained provisionally; browser
  experiment did not meet the live gate and is not a production fallback.
- CI inspection 41579361074 recovered the historical run logs and confirmed
  accepted/empty paired counts from runs #5/#8 and healthy real one-way counts
  from #7/#8. Evidence extraction is being hardened to exclude mock test output.
- Neither Amadeus credential nor Travelpayouts token is present in GitHub Actions.
  Need an authorized independent live-data provider within verified free quota.
- PR automation denial confirmed as repository Actions PR-creation policy.
  No PR created, no account policy changed. A human may open the prepared PR.
- Automatic diagnostic push trigger removed after provider rejection. Telegram
  remains deferred; main scheduled workflow and repository visibility unchanged.
- Remaining gates: new usable validated live quote, repeated real production
  history persistence, successful scan CI, PR, later Telegram delivery.

Final local verification for this research iteration: 31 tests pass under each
provider dependency, all workflows pass checksum-verified actionlint v1.7.7,
and git diff --check passes. User was asked only for an existing independent
provider account name, not secret values. Actual access is the remaining live
prerequisite; no paid source or billing was enabled. PR_DESCRIPTION.md now reflects
final implementation and explicitly unmet acceptance gates.

## Autonomous continuation: selected zero-spend API candidate

- Official Amadeus production documentation was inspected at revision
  6ecaad720eb122f765a2f205bf948a2a300c9111: payment/billing enrollment and automatic
  over-quota charges. Rejected autonomous enrollment under no-spending rule.
- Independent ordinary Kiwi page experiment 41582319498 returned HTTP 403 on the
  initial page. Stopped without retries, stealth or proxy changes; automatic
  trigger removed. No fare data was obtained.
- First-party access research 41582497237 confirms SerpApi Free is $0/month with
  250 monthly searches, and documents the two-stage returning-flight API.
  Selected this maintained API as the next optional candidate. No account created.
- Added providers/serpapi.py, strict synthetic response validation and account
  gate, atomic 2-search reservation, caps 8/day and 240/month, no refunds on
  ambiguous errors. It refuses paid/unknown account plans before flight queries.
  Production integration remains disabled pending actual response review.
- Readiness run 41582782842 reported credential_missing for SERPAPI_API_KEY.
  No search/account API request was made. No credential values were exposed.
- 36 tests pass locally against each Fli version. Workflow expressions pass
  actionlint. No new usable validated live fare, successful production scan or
  PR is claimed. Telegram remains deferred.

Precise external prerequisite: user creates/uses a SerpApi **Free** account and
sets GitHub Actions secret SERPAPI_API_KEY. Do not select a paid upgrade, supply a
card or paste keys in chat. Once supplied, run the prepared bounded candidate
probe, inspect actual fare semantics and rejected fields, and integrate only
if live validation succeeds. Same persisted fare DB must carry quota reservations
before any production scheduling. At 240 searches/month, no more than 120 complete
pair searches/month are budgeted (~54 days for a first 216-pair pass). Explain
quota-deferred triggers honestly; four-hour scheduler does not guarantee a live
query at every trigger or a fresh full-grid scan.


## Live retrieval and repeated persistence verified (supersedes missing-key blocker)

User supplied SERPAPI_API_KEY securely. The account's safe metadata is Free Plan,
plan_id free, zero monthly price, initial250 search balance. Updated account gate
to stable ID/zero-dollar price after display-name mismatch; no paid calls allowed.
Initial live source run41583877757 returned3 accepted candidates, lowestCAD2304
Jan25/Apr16. No checkout verification.

Integrated source run41584121588 completed2 actual tracker scans with history
restore/save between them. Observations12→13→17; all216pairs persisted; SQLite
integrityok; durable API reservations2→4. Jan27/Apr11CAD2560, durations1525/1565min.
Jan27/Apr19 lowestCAD2269, durations1525/1702min. This establishes functional live
retrieval and repeated durable history in the intended runner, not full-grid
freshness or checkout totals. No below1900fare was observed or Telegram sent.

Development flight-watch uses the four-hour cron plus Free API source, one pair
per trigger with persistent240/month and8/day caps. Core scanner now has source-
specific audit/health/failure classification. Local38tests pass per dependency.
Main is NOT updated; scheduled deployment requires review/merge. PR creation
remains externally blocked by Actions PR-creation policy. User can create the
prepared PR at github.com/ChhinaPB06/atq-flight-bot/pull/new/fix/roundtrip-provider-persistence.
Telegram remains deferred. Do not call all acceptance criteria complete.

## Latest scope and activation

User narrowed departures to Jan27–31 and returns80–90days later, retainingApr30
cutoff:54eligiblepairs. Earlier coverage metadata is archived and fare history
preserved; new coverage excludes out-of-scope diagnostics. Live run41588472235
scannedJan27/Apr20 andApr21 successfully. Lowest valid quote isCAD2245 onJan27/
Apr20 (83days), conservative total durations1525/1690minutes. These are search
quotes, not checkout-confirmed. Batch validation41589012699 passed, coverage6/54.

Initial sweep now attempts at most18pairs/trigger, within40searches/rollinghour,
120/day during firstpass and240/month; account mustremainFree/$0. Once all54
pairs have an API attempt, steady cap4searches/day allows2pairs/day so the monthly
Free allowance lasts. Stop/defer on rate/quota restrictions. Initial full sweep
costs at most108searches; this does not mean full-grid refresh every4hours.

At user's renewed autonomous request for an operational four-hour schedule,
main was activated by normal fast-forward push to9c98fd9, preserving history;
no force, branch-protection bypass or account policy change. Actions PR creation
remains disabled; no PR was fabricated. Telegram remains disabled/deferred.
A main-workflow configuration push event permits one immediate operational scan
as well as the unchanged '23 */4 * * *' cron; future ordinary source/docs pushes
will not trigger flight queries. Main workflow completion is to be observed.

## Latest execution checkpoint — native pilot and persisted coverage

Native pilot commit b0ce65c is pushed to the development branch; it is not
deployed to main. Ran all 54 offline tests successfully and actionlint on every
workflow. Ran the CLI twice against one explicitly synthetic email in a fresh
temporary database: one deduplicated unverified event, zero live observations.
This does not validate a real Google email template or a live verification.
The real pilot remains blocked on a user-enabled watch and approved .eml export;
no signed-in browser/mail connector is available. Telegram remains deferred.

Read-only flight-data snapshot 293b7855f676ca4d88a8a95d5a99f05be0cc80ac has
SQLite integrity ok and latest pair check 2026-11-03T12:11:35+00:00. Cumulative
API coverage is 38/54 (70.4%), with 34 valid-fare pairs, one duration-filtered
pair, three empty/unverified pairs and 16 unchecked. This is not fresh coverage
of all 54 pairs. Best observed quote remains CAD2074 Jan29/Apr21, durations
1810/1702 minutes, observed 06:31:27 UTC; not checkout-confirmed. No new provider
request or search-credit expenditure was needed for this execution checkpoint.

## Operational retry checkpoint

Main run41590235586 advanced to20/54completedAPIchecks,19with usable quote data
and1unverified no-data result (Jan28/Apr20). Unknown-error collapse was corrected;
no-data pair did not prevent later grid progress. Batch remained visibly degraded
for that unverified result; rolling-hour cap then deferred further checks.34pairs
remain for the active four-hour schedule. No full-grid completion claim.

New bestCAD2074 Jan29/Apr21,82days, conservative1810/1702minutes; Alaska/Qatar via
SEA/DOH. PreferredJan27bestCAD2233returnApr23,1780/1832minutes. All are observed
search quotes, not checkout-confirmed. No <=1900fare found. Current44tests plus
explicit empty-status regression bring final45passingtests. Active54pair CSV is
exported at/workspace/flight-search-54-pairs.csv. No extra API request is made for
this documentation/status correction; next searches follow four-hour cadence.
