# T9: embeddings for interpretation

## Approved specification and slices

The dispatched T9-B1 specification authorizes optional semantic examples and concept
suggestions, with SQL remaining the sole source of catalogue values. The unchanged
tool schema, explicit values, numeric bounds and negations take precedence. No
deterministic route may call embeddings; failures fall back to existing behavior.

1. Back up PostgreSQL, pin pgvector PG17, preserve all existing row counts, migrate.
2. Add a guarded 768-dimensional LangChain client and idempotent v7/anchor loader;
   test with a deterministic local embedder before the one authorized Google load.
3. Retrieve five examples and concept maxima before the single LLM decision;
   apply threshold/margin suggestions through the existing normalizer and expose debug.
4. Run Python tests, v7 selfcheck, text scanner and offline schema gate; rebuild
   the backend with Google embeddings enabled and verify `/ready`.

No chat inference, OpenRouter inference, mobile edits, pushes, secret output or volume
deletion are authorized. Tests use unittest and the approved `local_environment()`
connection mapping. Each slice is verified and committed separately.

## Database checkpoint

Backup: ignored `backups/t9-before.dump`, SHA256
`e6924174edbf5d3f6c2c9c1494b1de4dbe5f8018d14903933d5007fe36d953f7`.
Before: users 5, conversations 540, messages 1924, entries 68.
All 15 existing table counts matched before migration; migration was applied twice.
The initial pg17 tag used glibc 2.36, whereas the volume was created with 2.41.
Before data writes, switched to the coordinator-approved `pg17-trixie` digest in
Compose and CI. Container `ldd` confirms 2.41; database, postgres and template1
collation versions match their actual versions. All original data counts still match.
Implementation and final verification are in progress.
