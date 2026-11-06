# P2-B: executable public-text audit

Implemented an exit-coded CLI in `scripts/check_public_text.py`, retaining the existing scanner and adding field-path, SQL, traceback, error-class and raw-list checks. Exit 1 means a visible-text match or incomplete/unreadable source; exit 0 requires neither. Each finding identifies source, scenario/turn, public field path, matched rule and original text. `--report` writes a JSON ledger.

## Reproduce without inference or dotenv

Install the backend/test dependencies and provide the existing PostgreSQL catalogue connection through libpq process variables. The script never loads `.env`; the selfchecks use the existing acceptance runner with `IdealModel`, disabled embeddings/tracing, blocked outbound HTTP transports, and rollback-only transactions. A database is required: offline means no model/provider network calls, not an in-memory database.

```powershell
python scripts/check_public_text.py
python scripts/check_public_text.py --outputs '<local-scratch>/behavior/out_*/results.json' --report "$env:TEMP/public-text.json"
```

This run used `.venv-chat/Scripts/python.exe reports/agent_acceptance/run_t12_no_env.py scripts/check_public_text.py` with that outputs glob and a temporary JSON report. The existing wrapper reads only DB settings from the running container and installs a guard refusing `.env` opens. No backend, catalogue, frozen scenarios or database volumes were modified.

The default scans all v7/T10/T12/T14 scenarios in-process and the repository's `reports/agent_acceptance/t14_live` files. `--outputs` is repeatable; unmatched globs, invalid JSON, execution exceptions and incomplete scenarios fail closed. JSON metadata without responses is listed with zero counts. Markdown packs expose only their retained rendered prose; their PRODUCT CARD lines are evaluation serialization, not Android display labels. Full response JSON supplies product display labels and source notes; missing display fields cannot be reconstructed from a lossy Markdown pack.

Checked surfaces include answer, lead, question prompts/options/descriptions, suggestions, active-filter labels, comparison prose/labels/values, recommendation text/key values, product labels/source notes and glossary definitions. Machine IDs, debug traces, request text, option values and assumption values are excluded. Lowercase single-word enums still fail, but normal source prose such as ?on/off and modulating service? does not: the old substring rule produced false positives when coverage expanded to actual source notes.

Optional live mode supports 15 independent demo-account probes, including invalid/empty inputs, injection, lookup, comparison and overview:

```powershell
python scripts/check_public_text.py --live http://127.0.0.1:8000 --live-keyless
```

`--live-keyless` explicitly asserts that provider and embedding credentials are disabled on the target server. The client cannot disable remote credentials; without that flag it refuses to send probes. Live HTTP was not executed in this task, and no live/provider/device coverage is claimed.

## Verification

Nine new unit tests seed every requested leak category and cover nested surfaces, machine-metadata exclusion, source-note false positives, Markdown extraction, malformed/missing sources, exit codes and the live safety gate. Combined targeted run: 18 tests, 16 passed, 2 pre-existing DB-dependent skips (`test_public_text_audit`, `test_user_text`, `test_comparison_presentation`, with `PYTHONPATH=tests`). The complete DB-backed response audit is recorded below; acceptance correctness scores are separate from this text-only gate.

## Final observed results

Exit **1**, correctly caused by the stored experimental v2 outputs: **2,865 responses, 86,560 nonempty visible strings, 156 rule matches, 0 source/execution errors**. The 590 offline scenarios produced 975 responses and 32,364 strings with zero matches. Repository t14 packs contributed 85 response excerpts and 230 strings with zero matches; metadata JSON/JSONL files contained no response bodies. All 26 external files contributed 1,805 responses and 53,966 strings. Production v1, including `out_v15_v1` (131 responses / 3,665 strings), had **zero detected leaks**; these are stored outputs, not fresh paid validation.

Counts are physical occurrences: duplicate snapshots/prose across sources are counted separately; multiple matching rules or surfaces in one response are separate matches, not separate defects. All IDs below use the stored JSON path, whose `turns[n]` index is zero-based.

| Source | Responses | Strings | Matches |
|---|---:|---:|---:|
| `selfcheck/v7` | 760 | 24602 | 0 |
| `selfcheck/t10` | 66 | 3088 | 0 |
| `selfcheck/t12` | 87 | 2856 | 0 |
| `selfcheck/t14` | 62 | 1818 | 0 |
| `out_rec/results.json` | 7 | 260 | 0 |
| `out_rec2/results.json` | 7 | 293 | 0 |
| `out_v10/results.json` | 68 | 2291 | 0 |
| `out_v10_gemini-3.1-pro-preview/results.json` | 68 | 2217 | 0 |
| `out_v10_gemini-3.6-flash/results.json` | 68 | 2361 | 0 |
| `out_v10or_anthropic_claude-haiku-5.5/results.json` | 68 | 2180 | 0 |
| `out_v10or_deepseek_deepseek-v4.1-flash/results.json` | 68 | 2325 | 0 |
| `out_v10or_google_gemini-3.6-flash/results.json` | 68 | 2407 | 0 |
| `out_v10or_google_gemini-3.8-flash/results.json` | 68 | 2393 | 0 |
| `out_v10or_openai_gpt-6-luna/results.json` | 68 | 2345 | 0 |
| `out_v10or_openai_gpt-6-sol/results.json` | 68 | 2344 | 0 |
| `out_v11or_anthropic_claude-haiku-5.5/results.json` | 59 | 1244 | 0 |
| `out_v11or_deepseek_deepseek-v4.1-flash/results.json` | 59 | 1441 | 0 |
| `out_v11or_google_gemini-3.6-flash/results.json` | 59 | 1503 | 0 |
| `out_v11or_openai_gpt-6-luna/results.json` | 59 | 1481 | 0 |
| `out_v12or_google_gemini-3.6-flash/results.json` | 80 | 2439 | 0 |
| `out_v12or_qwen_qwen3.7-plus/results.json` | 80 | 2259 | 0 |
| `out_v13or_google_gemini-3.6-flash/results.json` | 91 | 2804 | 0 |
| `out_v14or_google_gemini-3.6-flash/results.json` | 85 | 2363 | 0 |
| `out_v15_v1/results.json` | 131 | 3665 | 0 |
| `out_v15_v2/results.json` | 131 | 1465 | 156 |
| `out_v8_off/results.json` | 69 | 2467 | 0 |
| `out_v8_on/results.json` | 69 | 2273 | 0 |
| `out_v9_confirm/results.json` | 69 | 2332 | 0 |
| `out_v9_off/results.json` | 69 | 2415 | 0 |
| `out_v9_on/results.json` | 69 | 2399 | 0 |
| `t14_live/failure_reasons.json` | 0 | 0 | 0 |
| `t14_live/heldout_v14.json` | 0 | 0 | 0 |
| `t14_live/pack_v14or_1.md` | 19 | 48 | 0 |
| `t14_live/pack_v14or_2.md` | 32 | 103 | 0 |
| `t14_live/pack_v14or_3.md` | 34 | 79 | 0 |
| `t14_live/screen_v14or.jsonl` | 0 | 0 | 0 |
| `t14_live/summary.json` | 0 | 0 | 0 |
| `t14_live/verdicts_v14or_1.json` | 0 | 0 | 0 |
| `t14_live/verdicts_v14or_2.json` | 0 | 0 | 0 |
| `t14_live/verdicts_v14or_3.json` | 0 | 0 | 0 |

## Exact leak ledger

All findings are in external `out_v15_v2/results.json`: **51 affected responses across 37 scenario IDs**. No backend fixes were made. Each row groups matching rules for one response; the source strings are validation/clarification text exposing internal state paths, field identifiers, or enum lists.

| Stored response ID | Public fields | Matched diagnostics | Matches |
|---|---|---|---:|
| `root.results[1]/L1-02.turns[0]` | `answer, clarification.message` | internal field path: state.site | 2 |
| `root.results[1]/L1-02.turns[1]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[1]/L1-02.turns[2]` | `answer, clarification.message` | internal field path: state.site | 2 |
| `root.results[2]/L1-03.turns[0]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[2]/L1-03.turns[2]` | `answer, clarification.message` | internal field path: state.site | 2 |
| `root.results[3]/L1-04.turns[1]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[3]/L1-04.turns[2]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[4]/L1-05.turns[0]` | `answer, clarification.message` | internal field path: view.limit | 2 |
| `root.results[6]/L1-07.turns[0]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[7]/L1-08.turns[0]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[8]/L1-09.turns[0]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[9]/L2-01.turns[0]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[12]/L2-04.turns[1]` | `answer, clarification.message` | internal field path: state.site | 2 |
| `root.results[12]/L2-04.turns[2]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[13]/L2-05.turns[0]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[14]/L2-06.turns[0]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[15]/L2-07.turns[0]` | `answer, clarification.message` | internal field path: view.limit | 2 |
| `root.results[17]/L2-09.turns[0]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[19]/L3-01.turns[0]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[20]/L3-02.turns[1]` | `answer, clarification.message` | internal field path: view.limit | 2 |
| `root.results[20]/L3-02.turns[2]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[22]/L3-04.turns[1]` | `answer, clarification.message` | internal field path: state.site | 2 |
| `root.results[24]/L3-06.turns[0]` | `answer, clarification.message` | internal field path: view.limit | 2 |
| `root.results[27]/L4-01.turns[0]` | `answer, clarification.message` | internal field path: state.site | 2 |
| `root.results[30]/L4-04.turns[1]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[31]/L4-05.turns[0]` | `answer, clarification.message` | internal field path: state.site | 2 |
| `root.results[31]/L4-05.turns[1]` | `answer, clarification.message` | internal field path: view.limit | 2 |
| `root.results[31]/L4-05.turns[2]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[32]/L4-06.turns[1]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[33]/L4-07.turns[1]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[35]/L5-02.turns[0]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[35]/L5-02.turns[1]` | `answer, clarification.message` | internal field path: view.limit | 2 |
| `root.results[37]/L5-04.turns[0]` | `answer, clarification.message` | internal field path: view.limit | 2 |
| `root.results[38]/L5-05.turns[0]` | `answer, clarification.message` | internal field path: view.limit | 2 |
| `root.results[40]/L5-07.turns[0]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[41]/L5-08.turns[0]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[42]/L6-01.turns[1]` | `answer, clarification.message` | internal field path: state.site | 2 |
| `root.results[42]/L6-01.turns[2]` | `answer, clarification.message` | internal field path: state.site | 2 |
| `root.results[44]/L6-03.turns[0]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[48]/L7-01.turns[1]` | `answer, clarification.message` | internal field path: state.filters.0.value | 2 |
| `root.results[48]/L7-01.turns[2]` | `answer, clarification.message` | internal field path: state.filters.0.value | 2 |
| `root.results[49]/L7-02.turns[0]` | `answer, clarification.message` | internal field path: state.site | 2 |
| `root.results[49]/L7-02.turns[2]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[53]/L7-06.turns[0]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[54]/L7-07.turns[1]` | `answer, clarification.message` | internal field path: state.site | 2 |
| `root.results[55]/L7-08.turns[1]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[55]/L7-08.turns[2]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |
| `root.results[55]/L7-08.turns[3]` | `answer, clarification.message` | internal field path: state.site | 2 |
| `root.results[56]/L7-09.turns[0]` | `answer, clarification.message` | internal field path: view.limit | 2 |
| `root.results[57]/L7-10.turns[0]` | `answer, clarification.message` | internal field path: state.site | 2 |
| `root.results[59]/L7-12.turns[0]` | `answer, clarification.message` | internal field path: context.hazard; internal field path: state.site | 4 |

Pending: optional keyless live HTTP verification; remediation of experimental v2 leaks belongs to its owner. No paid calls, external model reevaluation or Android display execution were performed.
