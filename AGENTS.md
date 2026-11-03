# Agent operating instructions

## Mission and current priority

Own the YYC–ATQ monitor through live validation and reviewable delivery. Read
PROJECT_STATUS.md and research/EXPERIMENTS.md before acting. The immediate target
is reliable, correctly priced and paired live round-trip retrieval. Telegram is
explicitly deferred by the user; do not let notification setup block provider work.

Preserve the user's flight constraints: YYC–ATQ return; one adult/economy; Jan
25–31 2027 departures, Jan 27 preferred; 60–90 nights; return by Apr 30,
mid-April preferred; all 216 valid pairs; each journey <=1860 minutes including
layovers; CAD; target <=1600, alert <=1900; record higher fares too. Keep the
four-hour free-first schedule, historical data and honest cumulative coverage.
No booking, payments, paid service signup, CAPTCHA/rate-limit bypass or main
force-push. Never print credentials or put them in evidence files.

## Research → experiment → evaluate loop

1. Observe: read current code, tests, working-tree changes, upstream source and
   actual failures. Separate observations from user-reported results and inference.
2. Orient: identify the failing boundary: environment, transport, provider health,
   payload parsing, outbound selection, return expansion, pricing, validation,
   persistence or CI. List competing explanations before changing code.
3. Decide: pick the smallest experiment that distinguishes those explanations.
   Record a falsifiable hypothesis, expected observations, exact command, request
   budget, timeout, and the acceptance gate it advances in research/EXPERIMENTS.md.
4. Act: run it, preserve exit status and sanitized evidence. Change one independent
   variable at a time. For provider comparisons use isolated stable/upstream venvs
   with identical dates, passenger/cabin, CAD locale and top_n.
5. Evaluate: mark keep, reject, inconclusive or blocked. A passing mock cannot
   resolve a hypothesis about a live response. Reject unsupported conclusions.
   Add a regression test for a reproduced defect, rerun affected checks, then
   continue the next useful experiment autonomously within the task budget.
6. Persist: update evidence and the next concrete experiment before switching
   approach or ending a turn. Preserve user changes. Use reviewable commits on the
   existing development branch; never blindly reset the shared working tree.

Do not repeat an unchanged failed command without a new diagnosis or meaningful
state change. Do not spend the budget adding frameworks while the next decisive
experiment is known. Research a new tool when it provides a missing capability;
verify primary sources, license, cost, credentials and applicability first. Use
existing session capabilities by default. Never install an unidentified package
based on a guessed name or attribute it to a person without evidence.

## Provider experiment budget and alternatives

Start with the previously successful Jan 25 / Apr 16 pair, then preferred Jan 27 /
Apr 15. Use top_n=1 for diagnostic experiments; increase only after useful data
and provider permission/limits are established. Limit a comparison to those two
pairs per version, serially with >=10 seconds between searches and a 120-second
outer timeout per experiment. Account for library retries/expansion requests;
never add unbounded outer retries or a fresh request loop after a block.

When raw data exists, capture sanitized fixtures and separately inspect initial
outbounds and selected-return expansion. Check returned currency, actual dates,
endpoints and both total journey durations. Establish price semantics from
upstream source and actual response evidence. Never fabricate a pair, assume
currency, sum separately quoted tickets into a round-trip booking, or promote a
calendar/cache quote to a live offer. Distinguish all-filtered fares from empty
data, parse errors, blocking, rate limiting and qualifying/nonqualifying prices.

If Fli is demonstrably unreliable after access works, evaluate a legitimate
independent source against the same gate. Document free quota and required
credentials. Separate one-way alternatives must be labeled separate tickets,
with independently observed prices/currencies/dates/durations; never present
an unobserved sum as a quote. Travelpayouts cache alone does not meet the gate.

## Completion gates (immutable without explicit user scope change)

- Live usable YYC–ATQ round-trip retrieval with validated currency, actual dates,
  both <=31h durations, documented price semantics and sanitized evidence.
- Repeated real scan preserves historical observations without overwrites and
  reports honest 216-pair coverage and realistic cycle time.
- Meaningful offline/provider tests and remote CI pass; an actual scheduled or
  manually dispatched scan demonstrates provider and persistence behavior.
- Telegram delivered once credentials are available (deferred, not passed).
- Clear setup/maintenance/troubleshooting docs, pushed development branch and PR.

Report each gate as passed, failed, blocked, deferred or unrun. No aggregate
"done" from unit-test count. No claim that the root cause is fixed without a
reproduction and successful live retest. Distinguish branch code from deployed
main, draft settings from applied settings, and prepared PR text from a real PR.

## External blockers

Inspect available runtime policy and credential metadata without values. A proxy
CONNECT 403 is not proof of zero inventory. Saving an allowlist draft is not
applying it. Git access does not prove GitHub API access. Request only the exact
remaining capability through supported settings, once; continue independent work.
After an actual settings change, rerun the blocked experiment. If independent
work is exhausted, state the blocker and next exact command instead of claiming
success or manufacturing a new framework to evade policy.

Use the existing isolated checkout; do not create worktrees unless requested.
Activate /workspace/venvs/atq-flight-bot for stable or
/workspace/venvs/atq-flight-bot-upstream for pinned upstream when present; otherwise
follow README setup. Agent instructions guide future turns when this checkout is
loaded; they do not create an unattended background agent or change system tools.
