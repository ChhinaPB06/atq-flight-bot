# Agent workflow research

## Primary sources inspected

- https://github.com/karpathy/autoresearch — README.md and program.md at
  228791fb499afffb54b46200aca536f79142f117. Implements fixed-budget experiments,
  a fixed evaluation target, baseline measurement and keep/discard decisions.
  Actual software is a GPU model-training experiment; its training dependencies
  are not applicable to this flight monitor. Adapt the experiment discipline,
  not its GPU runtime, unlimited loop, permission advice or reset commands.
- https://github.com/openai/openai-agents-python — README.md at
  e355d69152d4f4730dfb03b63dbce53e8d9f5d8c. Supports tools, guardrails, sessions,
  tracing and handoffs. Running it introduces a separate model-service runtime
  and credentials; installing it does not provide Google or GitHub authorization.
  Not selected for the current free-first repair task. No model API was invoked.

## Selection

Use the current coding agent with repository-level AGENTS.md and a committed
experiment ledger. Apply observe/orient/decide/act plus autoresearch-style
baseline/experiment/evaluate cycles. This is an adapted operating procedure,
not a claim to have installed or executed either external framework.

Keep hard live acceptance gates; preserve inconclusive and blocked results.
Optimize reliable validated retrieval, not number of passing synthetic tests.
Change approach when an experiment falsifies the current hypothesis.

## Unresolved framework identity

Public GitHub repository searches for `Bilawal Sidhu Orient`,
`orient agent framework`, `orient in:name agent`, `"Bilawal"`, and `"Sidhu" agent`
did not establish a specific Orient framework associated with Bilawal Sidhu.
Search results included OODA-loop descriptions (Observe, Orient, Decide, Act),
but that does not establish what he used or meant. General Google search failed
with proxy CONNECT 403. Do not invent a match or install an arbitrary similarly
named package. Revisit the attribution when public web search is available.
