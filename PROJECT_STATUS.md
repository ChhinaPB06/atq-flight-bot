# Flight bot status and decision log

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
