# P2-C: README Quick start on Linux CI

Scope: keyless backend reproduction, without paid inference or Android/device claims.
Workflow: `.github/workflows/quickstart-e2e.yml`; job **Quick start / Linux keyless**
(`quickstart-e2e`), on every push and pull request, Ubuntu latest, Python 3.12.

The runner copies `.env.example` to `.env`, runs `docker compose up -d --build`,
waits for `/ready` HTTP 200, runs the stdlib-only smoke script, and always tears
down its disposable Compose project with `docker compose down -v`.
The job supplies no secrets and explicitly empties both inference API keys.

## Local verification (2026-11-06)

Docker Desktop Linux containers, project `serie76-ci`, PostgreSQL port `55434`,
API port `18002`. Existing `.env` was never read or modified: all local Compose
commands explicitly used `--env-file .env.example -p serie76-ci`.
Process overrides set `COMPOSE_PROJECT_NAME=serie76-ci`, `POSTGRES_PORT=55434`,
`API_PORT=18002`, empty `OPENROUTER_API_KEY`/`EMBEDDING_API_KEY`, and
`LANGSMITH_TRACING=false`.

```text
docker compose --env-file .env.example -p serie76-ci up -d --build
python scripts/quickstart_smoke.py --base-url http://127.0.0.1:18002
docker compose --env-file .env.example -p serie76-ci down -v
```

| Step | Local result | Assertion |
|---|---|---|
| Build/start | PASS | Fresh isolated database volume and backend started |
| Readiness | PASS | HTTP 200 before and after restart |
| Both README users | PASS | Both public TEST ONLY credentials authenticate |
| Owner isolation | PASS | Other user cannot list, read or resume first user's session |
| README keyless example | PASS | Answer watts equal `motor_power_w` in extracted catalogue CSV; canonical product returned |
| Unknown code | PASS | Valid-format absent code returns not found, no substitute product |
| Partial/lowercase | PASS | Both resolve to canonical code with visible interpretation assumption |
| Free-language query | PASS | Exact documented HTTP 503 JSON, including `error_code: not_configured` |
| Sessions/messages | PASS | Owner lists sessions and their messages; saved answer matches response |
| Restart/resume | PASS | Same token and session work; prior messages unchanged, exactly one turn appended; isolation retained |
| Teardown | PASS | Only `serie76-ci` containers/network/volume removed |

Initial smoke development caught a UTF-8 BOM in the CSV (now read with
`utf-8-sig`) and an invalid `/Z` unknown-code fixture (now valid-format `/A`).
The final local smoke exited zero. No application code or validated data changed.

## GitHub verification

Verified implementation commit: `400d5c22daec9030e9bd8b6afe01bbcbd5306cc5`.
PR #10 [Ubuntu pull-request run](https://github.com/SamuelCharry/serie76-assistant/actions/runs/42234532660)
passed in 1m06s; the [push run](https://github.com/SamuelCharry/serie76-assistant/actions/runs/42234523930)
also passed (58s). `gh pr checks 10` reports **Quick start / Linux keyless: pass**
for both events. Other pre-existing CI jobs were still pending at that observation;
this is not a claim that every PR check passed.

| GitHub workflow step | Result |
|---|---|
| Checkout and Python 3.12 setup | PASS |
| Copy README configuration with empty key | PASS |
| Docker Compose build/start | PASS |
| Readiness HTTP 200 | PASS |
| Smoke: both logins, isolation, CSV value, unknown code, partial/lowercase assumptions, documented error JSON, history, restart/resume | PASS (each assertion group printed PASS in the run log) |
| Failure diagnostics | SKIPPED (no failure) |
| Disposable containers/network/volume teardown | PASS |

This establishes GitHub-hosted Ubuntu keyless backend reproduction. Android,
device, macOS and real-provider acceptance remain outside this test.
