# Agent acceptance

> Historical Google cohorts below are retained unchanged. Current OpenRouter results, the adopted improvement and repair boundaries are in [the paired v17 report](../../reports/submission/P2-A.md) and [README](../../README.md#models-design-and-limitations).

Production A+ client, model `gemini-3.6-flash`, Google OpenAI-compatible endpoint. OpenRouter calls: 0. Cohorts overlap and must not be summed as independent cases. Costs below are the exact summary values in USD; conservative reservations are not an invoice.

| Cohort | Passed/scenarios | Quality failures | Provider-only failures | Provider | Conservative charge USD | Usage-based charge USD |
|---|---:|---:|---:|---|---:|---:|
| v1 | 25/27 | 2 | 0 | google-openai-compatible | 0.195906 | 0.06138375 |
| v2 | 38/43 | 2 | 3 | google-openai-compatible | 0.6330255 | 0.09101775 |
| v3 | 46/51 | 3 | 2 | google-openai-compatible | 0.428946 | 0.10152075 |
| v4 | 50/55 | 1 | 4 | google-openai-compatible | 0.738165 | 0.11677725 |

Exact summaries: [v1](data/agent-v1-summary.json), [v2](data/agent-v2-summary.json), [v3](data/agent-v3-summary.json), [v4](data/agent-v4-summary.json).

Offline check: `python scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_v4.json`.

Historical reproduction, requiring explicit paid-call approval: run `scripts/agent_acceptance.py run --cohort NEW --cases config/agent_acceptance_cases_v4.json`, then `scripts/agent_acceptance.py report --cohort NEW --cases config/agent_acceptance_cases_v4.json`. Use a new cohort to preserve frozen records. No inference was run during cleanup.

The v4 strict power-limit case failed; its prompt correction has not been rechecked with a real LLM. Four v4 cases remained unevaluated after provider errors. These old cohorts do not establish current OpenRouter or Android acceptance; see the current evidence above.

[Original archive](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/agent_acceptance).

Use the activated generic backend environment from [test setup](../wiki/en/testing.md#run-locally); it installs requirements-dev.txt.
