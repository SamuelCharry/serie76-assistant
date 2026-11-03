# Native Android fidelity adjudication

Artifact: mobile/android. Approved comp: .impeccable/mocks/conversations-c.png. Current final capture: .impeccable/review/conversations.png (round-3 API35 emulator, 1080x2400). Fixtures exist only in androidTest. Original failed score 70.3% is retained in diff/hero-before-fixes. Current score 76.91% and all regional flags remain in diff/hero/report.json.

## Evidence and decisions

The independent shipped Impeccable native reviewer inspected the eight current captures and source code. It scored six of seven fixes resolved and the remaining evidence packaging fix partial. It explicitly found no further material layout repair and confirmed no material regression. This file records the native adjudication requested by that reviewer; it does not alter the numerical comparison or claim an automatic pass.

| Flag | Native adjudication |
|---|---|
| status | System-owned Android clock/icons exist in full screenshots. Their time, glyphs and inset differ from generated reference; do not paint fake native chrome. MainActivity explicitly selects light-system-bar styling. |
| brand | Removed by the independent review's explicit floor fix. Recorded in direction contract. Restoring it solely to satisfy pixel matching would revert that requested fix. Product identity remains in launcher/chat. |
| heading | Dominant Conversations title restored at 42sp/48sp with native Roboto; reviewer scored hierarchy resolved. Text wraps under font scaling. |
| new-conversation | Visible native Material button, correct action and location. Dark text intentionally replaces generated white-on-lilac to meet contrast. Semantics and click tested in emulator. |
| first-title/preview | Dynamic conversation title/preview, date upper right. Source content cannot be replaced with hardcoded generated records just to match letter pixels. Reviewer scored ordering/position resolved. |
| gesture-inset | Native Android gesture bar is present in full current captures. It is not a raster or manually positioned control. |

## Final package

diff/final contains the final Conversations comparison, using the same final capture as hero-repro.png; therefore its report and side-by-side legitimately match diff/hero. It is not a second independent measurement. The rest of the final screen matrix is in this directory: conversations-empty, backend-error, chat-sent, chat-keyboard, product-font130, comparison and developer-debug. No browser detector was used on native source.

The CLI hero phase is now closed by an explicitly recorded user-accepted override. The user stated: 'Apruebo la adaptación nativa final y acepto sus diferencias respecto a la maqueta C' (see native-approval.json). The automatic gate still failed: gate.ok=false and the 76.91% result/flags remain intact. The CLI's force operation records that accepted deviation; it does not manufacture an automatic pass. The native-only responsive override likewise uses real phone/font-scale/keyboard evidence rather than a fabricated browser desktop capture. Native adjudication and user acceptance remain separate from automatic pixel scoring. This distinction must remain visible in reports/mobile.

Backend routing/model evaluation is a different scope: real PostgreSQL and API contracts are verified with controlled routing, but no real OpenRouter evaluation or physical device validation is claimed.
