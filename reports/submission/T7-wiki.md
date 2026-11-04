# T7 wiki and README

Updated both languages of agent, API, Android, testing, patterns and operations; added six Spanish interview questions and updated both README status tables. Documentation covers the additive interaction contract, deterministic Submit/filter removal, optional suggestions, comparison layouts, greeting, eight exploratory policies, bounded retry/fallback and the connection lifetime fix.

Sources: approved [backend report](T7-backend.md), [Android report](T7-android.md), and committed [HTTP JSON](T7-interactions.json) / [scenario JSON](T7-scenarios.json), on `release/submission` after Android merge `2c2dc3b`. The displayed question, comparison row, greeting and response excerpt match the captured JSON; shell and PowerShell submission examples decode to equivalent requests. No catalogue values were invented.

Validation for this documentation task:

- T3 relative-link checker: `python scripts/check_docs_links.py` passed, zero broken links/anchors.
- UTF-8 JSON excerpt/request checks passed in both languages; each testing page retains exactly one `v6 real-model result: pending coordinator run` placeholder.
- `git diff --check` passed. Changes are Markdown only; no application code, Android source, catalogue, environment or migrations changed.

Previously recorded test counts are explicitly attributed to the backend and Android reports; these suites were not rerun for this documentation edit. No inference, live preflight, rebuild, push or external publication was performed. Real-model v6 remains for the coordinator; device visual acceptance and the deployed first-tap reproduction are not claimed by the local transport evidence.
