# T10-E: contrastive bank and opt-in prompt candidates

Prepared only: no inference, embeddings or bank load. Existing examples and default prompt are unchanged. These are training candidates, not a new held-out evaluation cohort.

## Files and use

- `config/example_bank_contrastive_t10.json`: 60 pairs / 120 unique self-contained requests, 10 pairs each for bounds, remove versus negate, hazard, objective, reference and compound operations. 48 pairs English, 12 Spanish or predominantly Spanish. Numeric values are requested constraints, not catalogue facts; reference codes carry no performance values.
- `config/prompt_variants_t10.json`: hypotheses and additive prompt suffixes.
- `backend/conversation/prompt_variants.py` and `agent.py`: `AGENT_PROMPT_VARIANT` unset, empty or `current` returns the original prompt; select `state_operations`, `references` or `compound_questions` explicitly. Unknown values fail explicitly.
- `Dockerfile`: packages the variant config for opt-in runtime use.
- `tests/test_prompt_variants_t10.py`: frozen SHA-256/byte identity, loading all candidates, invalid selection, 60 pairs/120 retained interpretations and canonical schema validation.

Preview without model, database or credentials (PowerShell):

```powershell
$env:OPENROUTER_EMBEDDING_MODEL=''
$env:PYTHONPATH=(Get-Location).Path
python scripts/load_example_bank.py --dry-run --cases config/example_bank_contrastive_t10.json
```

Existing loader input remains `config/agent_acceptance_cases_v7.json`; selecting the new source is explicit. The bank stores text without conversation context, so the new texts include any prerequisite history instead of relying on dropped metadata. The two members of a pair are independent examples, not a sequential conversation.

Dry-run: 220 pending texts = 120 examples + 100 existing anchor inputs, 10,063 estimated tokens, USD 0.002013, 7 batches, `scope=input_only`, `existing_vectors_checked=false`, `model=null`. This is a UTF-8-byte upper estimate at the loader's configured USD 0.20/million rate, not a provider quote or a claim that these anchors are missing from a configured database.

## Hypotheses

- `state_operations`: Explicit delta classification reduces bound replacement, negation and objective persistence errors seen in v10/v11.
- `references`: Separating relative search from lookup/comparison reduces accidental comparison and invented reference thresholds.
- `compound_questions`: Decomposing supported and unsupported clauses before the single decision reduces lost lookups and fabricated commercial or rating answers.

## Verification

- New offline unit tests: 4/4 passed.
- Tool schema: 107 enum values (limit 108), 6 arrays, depth 7; exit 0.
- `PYTHONPATH` set to repo root; `scripts/check_public_text.py`: exit 0. This file defines audit functions rather than a standalone scanning main; actual public-text assertions also execute throughout the DB suite and acceptance checks.
- v7 selfcheck: 453/453 passed, exit 0.
- T10 selfcheck: 48/48 passed, exit 0.
- Default bank dry-run remains 758 input texts (658 examples + 100 anchors), exit 0; contrastive dry-run above also exits 0.
- Full DB first attempt: 571 tests, one harness error, two skips, exit 1. The isolated copy omitted `docker-compose.yml`; the source-inspection test also requires `.env.example`. Copied these non-secret files without touching `.env`; full rerun passed: 571 tests run, 569 passed and two skipped, zero failures/errors, 195.708 seconds, exit 0. The failed initial attempt is retained in `reports/t10e-unittest.log`; successful rerun is `reports/t10e-unittest-rerun.log`.

DB gates use a source snapshot in `/tmp/t10e` inside the existing backend container, with read-only extracted/raw data links and existing container DB environment. No `.env` is copied or read. Inference keys/models and embeddings are disabled for those commands; selfchecks use scripted decisions. Nothing is committed or loaded into the real example bank.

Final gate status: all final commands exit 0. The first incomplete-harness attempt exited 1 and was corrected and rerun in full; it is not counted as a pass. No claim of provider quality improvement is made; inference/embedding loading and independent held-out evaluation remain pending authorization.

Selfcheck commands (same isolated container environment):

```text
python -m unittest discover -s tests                         # SERIES76_TEST_DB=1
python scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_v7.json --config config/agent_acceptance_v7.json
python scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_t10.json --config config/agent_acceptance_t10.json
python scripts/check_tool_schemas.py
python scripts/check_public_text.py                         # PYTHONPATH=repository root
```
