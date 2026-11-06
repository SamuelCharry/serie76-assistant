# GitHub Wiki publication

`docs/github-wiki/*.md` is the editorial source for the separate GitHub Wiki repository. Keep the Spanish defense guide at `docs/wiki/es/defensa-entrevista.md` identical to `docs/github-wiki/Guion-de-sustentacion.md`.

1. Review the current implementation and evidence before changing claims.
2. Edit the source pages. Use absolute Wiki links so navigation works both in `main` and in the published Wiki; retain existing page names.
3. Validate source paths, Wiki targets, Markdown links and diagrams. Commit the source changes to `main`.
4. In a clean clone of `https://github.com/SamuelCharry/serie76-assistant.wiki.git`, copy the Markdown sources, review the diff, commit and push its current branch. Never replace its Git metadata.
5. Verify the remote commit and reread the published content. A push to `main` alone does not update the Wiki.

The application tag stays unchanged for documentation-only updates. Keep real-model, offline, emulator and physical-device evidence distinct; no inference is needed to publish these pages.
