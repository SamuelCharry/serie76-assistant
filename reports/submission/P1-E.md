# P1-E: recorded-decision replay regression investigation

**The reported 28/45 to 17/45 drop is not reproducible.** Fresh unchanged runs
at both Plan B commits and the current source all pass **28/45 conversations**
and **73/91 turns**. The **17** is the number of failing conversations, not
passing conversations. Both [P1-C](P1-C.md) and [P1-D](P1-D.md) already report
28 passing and 17 failing. Interpreting a failure count as a pass count appears
to explain the task premise; there is no supplied 17-passing artifact to verify.

Date: 2026-11-05. Main checkout remained on `release/submission`; initial
`git pull --ff-only` reported up to date at `9f5d3c4`. Backend, scripts, tests
and config are identical between that HEAD and P1-C `31f4329` (`git diff`
on those four directories is empty).

## Reproduction and classification

| Source | Conversations passed / failed | Turns passed / failed | Replay exit |
|---|---:|---:|---:|
| `4906b62` (Plan B implementation) | 28 / 17 | 73 / 18 | 1 |
| `95d0a50` (Plan B documented result) | 28 / 17 | 73 / 18 | 1 |
| `9f5d3c4` (current HEAD, same tested code as P1-C) | 28 / 17 | 73 / 18 | 1 |

**Newly failing conversations: zero. Classes (a)/(b)/(c): 0 / 0 / 0.**
There are no eleven new failures to classify. No backend fix, regression test,
replay assertion change or frozen expectation change is justified by this
comparison. The 17 historical failures remain failures; numeric, provenance
and integrity checks were neither disabled nor weakened. This is a diagnostic
recorded-decision replay, not a fresh model evaluation.

Comparison covers all 45 conversations and all 91 turns. Every conversation
status, turn verdict and assertion failure list is unchanged. All semantic
fields are identical between the two Plan B commits. Between Plan B and HEAD,
44 turns in 25 conversations have differences:

- **41 turns in 23 conversations:** T15 adds the published-data scope and,
  where relevant, explicitly discloses excluded N/A rows. Product snapshots,
  candidates, eligibility, numeric checks and verdicts are unchanged. These
  are expected changes (b), but cause **zero new failures** and require no
  assertion updates.
- **L7-05 turn 1:** P1-C resolves the unknown full code via SQL before the
  recorded model decision, returns an explicit not-found clarification, and
  stores pending part-number clarification rather than overview focus. Turn 2
  differs only in that incoming context; its rendered result is unchanged.
  Expected change (b), both turns still pass.
- **L7-06 turn 1:** P1-C detects the one-character incomplete code via SQL and
  offers the existing full code for confirmation. It does not silently select
  the product. The recorded model decision is bypassed; the turn still passes.
  Expected change (b), requiring no assertion update.

Thus the observed non-regressing changes can be described as (b) in 25
conversations; that must not be confused with the **0/0/0 classification of
new failures** requested above. No new sentinel/status/input-limit failure
appears. The five unavailable-decision sentinels documented in T14 remain
unchanged, including the historically passing L4-02 conversation.

The [machine-readable comparison](p1e-evidence/comparison.json) includes every
query, per-turn verdict/failure list, SHA-256 of the entire stable turn, and
field-level diffs. Only generated `elapsed_s`, `latency_ms`, `session_id` and
`message_id` fields are excluded from semantic comparison. Full product
values, provenance, candidates, state and traces are compared. The
[comparison script](p1e-evidence/compare.py) regenerates it without database
or network access.

## Per-conversation results

P/F sequences list each turn in order and are identical at all three commits.
`Scope` means the T15 published-data/N/A disclosure described above. A dash
means no semantic change; timing and generated identity fields are ignored.

| Conversation | Turns at all three commits | Changed turns / explanation |
|---|---|---|
| L1-01 | P P | - |
| L1-02 | P | 1: Scope |
| L1-03 | P P | 1, 2: Scope |
| L1-04 | P P | 1: Scope |
| L1-05 | P | - |
| L1-06 | P | - |
| L1-07 | P P | - |
| L2-01 | P P | 1, 2: Scope |
| L2-02 | F | - |
| L2-03 | P | - |
| L2-04 | P P | 1, 2: Scope |
| L2-05 | P | - |
| L2-06 | P | - |
| L2-07 | P P | 1, 2: Scope |
| L2-08 | P P | 1: Scope |
| L2-09 | F P | 2: Scope |
| L3-01 | P P P | 1, 2: Scope |
| L3-02 | P F | - |
| L3-03 | P F | 1: Scope |
| L3-04 | F | - |
| L3-05 | P | - |
| L4-01 | P P P | 1, 2, 3: Scope |
| L4-02 | P P P | 1, 2: Scope |
| L4-03 | P P F | 1, 2, 3: Scope |
| L4-04 | P P P | 1, 2: Scope |
| L4-05 | P P P | - |
| L4-06 | P P P | 1, 2, 3: Scope |
| L5-01 | P P | - |
| L5-02 | F P | 1, 2: Scope |
| L5-03 | P P | - |
| L5-04 | P P | 1, 2: Scope |
| L5-05 | P F | - |
| L6-01 | P | - |
| L6-02 | P | - |
| L6-03 | F | - |
| L6-04 | F | - |
| L7-01 | P P P F | 2: Scope |
| L7-02 | P F P P | 1, 2: Scope |
| L7-03 | P P F | 1: Scope |
| L7-04 | P F | 2: Scope |
| L7-05 | P P | 1: SQL not-found; 2: incoming clarification context |
| L7-06 | P P | 1: SQL near-match confirmation |
| L7-07 | F P | 1, 2: Scope |
| L7-08 | F F | - |
| L7-09 | P P F P | 1, 2: Scope |

## Gates on the same source

| Gate | Result | Exit |
|---|---|---:|
| Full PostgreSQL unittest (direct) | 660 run, 658 passed, 2 optional OCR skips; 347.273 s | 0 |
| `run_t14_gates.py` overall | All required stages passed | 0 |
| Runner PostgreSQL unittest | 660 run, 658 passed, 2 optional OCR skips; 325.302 s | 0 |
| v7 / T10 / T12 / T14 | 453/453 / 48/48 / 47/47 / 42/42 | 0 each |
| Tool schema | 5,520 bytes, 108 enum values, 0 forbidden nodes | 0 |
| Public text | Passed | 0 |
| Ranking | 40 queries, 2,720 judgments; NDCG@3 0.965378, returned compliance 1.0, no safety failures | 0 |
| Diagnostic replay inside runner | 28/45 conversations, 73/91 turns | 1 |

The runner explicitly excludes diagnostic replay from its overall exit code;
its exit 0 is not replay success. Its final replay is semantically identical
to the standalone HEAD run after excluding only the four generated fields
listed above. Every file in the runner's code manifest matched the working
source after completion. Frozen v6/v7/T10/T12/T14 expectations remain unchanged.


## Reproduce without inference or private environment files

The detached worktrees were created under the Windows temporary directory:
`%TEMP%/series76-p1e-4906b62` and `%TEMP%/series76-p1e-95d0a50`.
Commit `4906b62` predates the checked-in captured decisions and no-env wrapper;
only the identical current `flash_replay_cases.json` and `run_t12_no_env.py`
were copied there. Its backend, scoring adapter and oracle remained unchanged.
The adapter/oracle/config have no diff between `4906b62` and `95d0a50`.
An initial launch at `4906b62` exited 2 because the wrapper was absent; the
completed run above is the rerun after copying that evaluation-only file.

Use the existing backend virtualenv executable by absolute path for worktrees.
For each checkout, run its own wrapper with these arguments (absolute output
path for worktrees):

```text
reports/agent_acceptance/run_t12_no_env.py scripts/agent_acceptance.py selfcheck --cases reports/agent_acceptance/t14_oracle_pre_fix/flash_replay_cases.json --config config/agent_acceptance_t14.json --evidence <output.json>
```

Store the three outputs as `4906b62.json`, `95d0a50.json` and `head.json` beside
`p1e-evidence/compare.py`, then run that script. The historical replay source
`replay_t14.py` is a trace-recovery script, not the scoring entrypoint; rerunning
trace recovery was unnecessary because all original recorded decisions and
assertions were already available and held constant.

The no-env wrapper reads only database connection settings from the running
backend container into memory, clears provider keys, disables embeddings and
tracing, and installs a hook that rejects `.env` reads. No `.env` was read, no
inference was run, and the existing catalogue volume was preserved.

The two verification commands used the main checkout and the same code:

```text
.venv-model-eval/Scripts/python.exe reports/agent_acceptance/run_t12_no_env.py -m unittest discover -s tests
.venv-model-eval/Scripts/python.exe reports/agent_acceptance/run_t14_gates.py
```

Raw replay outputs, logs and the complete fresh runner artifacts are retained
locally at `C:\Users\nrir\AppData\Local\Temp\series76-p1e-evidence-20261105-1938`.
The [verification manifest](p1e-evidence/verification.json) records source
commits, input/output hashes, exit codes and gate summaries. Historical tracked
T14 artifacts are restored after archival, rather than replaced by this run.

No production/harness assertion files were edited. The only additions are this
report, its comparison utility and compact audit evidence. Remaining work is
the existing 17 diagnostic failures and separately documented live/device
limitations; no new regression is established by this investigation.
