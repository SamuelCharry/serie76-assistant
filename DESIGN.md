---
name: Series 76 Android
description: A native conversation workspace with compact history and Konecto lilac.
colors:
  primary: "#BD7BFF"
  ink: "#211A2B"
  primary-container: "#ECE4F6"
  dark-action: "#4C315E"
  background: "#FAFAFC"
  background-ink: "#25232A"
  surface: "#FFFFFF"
  surface-variant: "#EFEEF4"
  muted-ink: "#66616F"
  outline: "#807887"
  divider: "#DFDCE5"
  error: "#9E2036"
  error-container: "#FFE9ED"
  error-ink: "#6E1324"
typography:
  headline:
    fontFamily: "Roboto (Android system sans-serif)"
    fontSize: "32sp"
    fontWeight: 400
    lineHeight: "40sp"
    letterSpacing: "0sp"
  title-large:
    fontFamily: "Roboto (Android system sans-serif)"
    fontSize: "22sp"
    fontWeight: 500
    lineHeight: "28sp"
    letterSpacing: "0sp"
  title-medium:
    fontFamily: "Roboto (Android system sans-serif)"
    fontSize: "16sp"
    fontWeight: 500
    lineHeight: "24sp"
    letterSpacing: "0.15sp"
  title-emphasis:
    fontFamily: "Roboto (Android system sans-serif)"
    fontSize: "16sp"
    fontWeight: 600
    lineHeight: "24sp"
    letterSpacing: "0.15sp"
  title-small:
    fontFamily: "Roboto (Android system sans-serif)"
    fontSize: "14sp"
    fontWeight: 500
    lineHeight: "20sp"
    letterSpacing: "0.1sp"
  body:
    fontFamily: "Roboto (Android system sans-serif)"
    fontSize: "16sp"
    fontWeight: 400
    lineHeight: "24sp"
    letterSpacing: "0.5sp"
  body-medium:
    fontFamily: "Roboto (Android system sans-serif)"
    fontSize: "14sp"
    fontWeight: 400
    lineHeight: "20sp"
    letterSpacing: "0.25sp"
  body-small:
    fontFamily: "Roboto (Android system sans-serif)"
    fontSize: "12sp"
    fontWeight: 400
    lineHeight: "16sp"
    letterSpacing: "0.4sp"
  label:
    fontFamily: "Roboto (Android system sans-serif)"
    fontSize: "14sp"
    fontWeight: 500
    lineHeight: "20sp"
    letterSpacing: "0.1sp"
rounded:
  "small": "12dp"
  "row": "16dp"
  "medium": "20dp"
  "drawer-end": "24dp"
  "large": "28dp"
spacing:
  "4": "4dp"
  "8": "8dp"
  "10": "10dp"
  "12": "12dp"
  "16": "16dp"
  "20": "20dp"
  "24": "24dp"
components:
  button-send:
    backgroundColor: "{colors.dark-action}"
    textColor: "{colors.surface}"
    size: "48dp"
  button-tonal:
    backgroundColor: "{colors.surface-variant}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
  button-text:
    textColor: "{colors.dark-action}"
    typography: "{typography.label}"
  field-composer:
    backgroundColor: "{colors.surface-variant}"
    textColor: "{colors.ink}"
    rounded: "{rounded.large}"
    padding: "16dp 10dp 10dp 20dp"
    typography: "{typography.body}"
  row-selected:
    backgroundColor: "{colors.primary-container}"
    textColor: "{colors.ink}"
    rounded: "{rounded.row}"
    padding: "12dp 16dp"
  card-product:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.row}"
    padding: "16dp"
  panel-error:
    backgroundColor: "{colors.error-container}"
    textColor: "{colors.error-ink}"
    rounded: "{rounded.medium}"
    padding: "16dp"
  bubble-user:
    backgroundColor: "{colors.surface-variant}"
    textColor: "{colors.ink}"
    rounded: "{rounded.medium}"
    padding: "16dp"
---
# Design System: Series 76 Android

## Overview

**Creative North Star: "The Native Conversation Workspace"**

A quiet, Gemini-inspired conversation shell puts technical dialogue on a near-white canvas. Charcoal text, neutral tonal surfaces and restrained plum emphasis carry the hierarchy. Compact history lives in a left drawer; the rounded composer remains the primary working control.

This records the approved replacement of composition C, as implemented in Kotlin/Compose. Native Material 3 typography, controls, insets and Android system bars are deliberate approved adaptations. Layout uses dp and type uses sp; these are native units, not CSS pixels. The documented scope is a light phone interface, with no implemented dark/dynamic palette or verified tablet layout. UI fixtures establish rendering and interaction evidence; they do not establish a live LLM or physical-device result.

**Key Characteristics:**
- Near-white canvas with neutral tonal input and navigation surfaces.
- Compact native navigation, scalable typography and quiet plum actions.
- Technical context retained in outlined results and synchronized comparison columns.
- Loading, empty and recovery states within the same hierarchy.

## Colors

Konecto lilac anchors the identity while neutral tones and deep plum make the working surfaces readable. The frontmatter records explicit Theme.kt overrides; other Material color roles retain library defaults.

### Primary
- **Konecto Lilac** (`primary`): retained identity role; never substitute it for the dark action ink on small light-background text.
- **Selection Lilac** (`primary-container`): selected conversation row.
- **Deep Plum** (`dark-action`): greeting emphasis, send background, text actions, input cursor and loading indicator.

### Neutral
- **Near White** (`background`): chat canvas and compact app bar; `background-ink` supplies its native content role.
- **Reading White** (`surface`) and **Charcoal Plum** (`ink`): technical reading cards and strong text.
- **Quiet Neutral** (`surface-variant`): composer, drawer, starter pills, user bubbles and comparison labels.
- **Muted Ink** (`muted-ink`): source text, dates, subtitle and placeholder.
- **Outline** (`outline`) and **Fine Divider** (`divider`): Material boundaries and technical result lines.
- **Catalogue Error**, **Error Wash** and **Error Ink** (`error`, `error-container`, `error-ink`): unavailable catalogue status and recovery panels.

**The Dark Action Rule.** Use deep plum for small action text and the send control; keep lilac as identity and selection rather than light-background body text.

The New chat FilledTonalButton currently inherits Material's default secondary-container roles because Theme.kt does not override them. Its default-derived lavender is not a new Konecto primitive.

## Typography

**Display and Body Font:** native Android system sans through Material 3 `Typography()`; Roboto is the reference emulator rendering. No font file ships. The approved native adaptation explicitly retains this family for the greeting.
**Label/Mono Font:** Material labels; native monospace only for debug JSON.

### Hierarchy
- **Headline:** Material headlineLarge for the greeting; normal second line and semibold plum Hello span.
- **Title large:** drawer identity and empty-state titles, medium emphasis.
- **Title medium:** compact chat title, result identifiers and comparison heading; product identifiers use the title-emphasis weight.
- **Title small:** Recent section label.
- **Body:** messages, composer, drawer titles and domain subtitle.
- **Body medium:** result attributes, recovery messages and loading text.
- **Body small:** dates, source disclosure and comparison instructions; debug JSON uses the same metrics with monospace.
- **Label:** assistant identity, text actions and native buttons.

**The Context Stays Visible Rule.** Preserve complete technical identifiers, units, N/A and source disclosure; keep native font scaling instead of shrinking data to force a row to fit.

## Layout

Chat fills the available phone window. A compact native TopAppBar sits above the scrollable dialogue. The empty greeting receives a top inset of 22% of available content height, clamped between 32dp and 144dp, and disappears while the keyboard is visible. Two starter pills wrap through FlowRow. They fill and focus the draft without submitting it.

The message list uses 20dp horizontal and 16dp vertical padding with 24dp between items. The bottom composer area uses 16dp horizontal and 12dp vertical padding, navigation-bar and IME insets. The field grows from two to five lines. User bubbles align right with a 320dp maximum width. Assistant prose reads directly on the canvas.

The modal drawer occupies 84% of its parent width with 12dp horizontal inset. History rows use 16dp horizontal and 12dp vertical padding, 4dp internal and inter-row spacing, a two-line ellipsized title and a date. The selected row receives tonal lilac. History is a compact list, with paging and recovery as needed.

Comparison keeps the specification column fixed while all product columns share a horizontal scroll state. At font scale 1, label columns are 148dp and product columns 216dp, with 96dp headers and 76dp rows; dimensions multiply by fontScale clamped to at least 1. No tablet breakpoint has been implemented.

## Elevation & Depth

Tonal layering and fine technical outlines provide the main depth. No custom hard shadow or shadow scale is defined. Native Material components retain their own elevation and state layers; the drawer overlays chat with an onSurface scrim at 38% alpha. Do not remove native modal separation to enforce an absolute flatness rule.

**The Native Feedback Rule.** Retain Material interaction feedback and Android animation scaling. Debug surface navigation uses a 180ms Compose crossfade; drawer motion and message scrolling use native Compose behavior.

## Shapes

Soft geometry distinguishes interaction from reading. Theme small, medium and large corners are recorded in frontmatter. The composer uses large corners; product cards and selected history rows use row corners; user bubbles, comparisons and error panels use medium corners. Drawer corners are rounded only on the trailing edge. Native tonal buttons are pills and the send button is circular. Technical cards retain a fine 1dp outline; a border prohibition would contradict the actual reading system.

## Components

### Buttons

Quiet native actions. FilledIconButton sends with a 48dp circular target, deep plum background and white arrow. Blank, pending, loading, failed-history or reconciliation states disable sending. Disabled fill uses onSurface at 12% alpha and disabled icon at 38%. The vector arrow is 24dp with a 2-unit round-capped stroke. Text actions use deep plum; starter FilledTonalButtons use quiet neutral and charcoal. Drawer New chat uses native default tonal roles, 20dp horizontal and 12dp vertical content padding. Native Material press, focus and accessibility semantics remain authoritative.

### Inputs / Fields

The broad tonal composer has no outlined-field box or floating label. BasicTextField uses the body role, Ask Series 76 placeholder and a deep-plum cursor. Padding and corner values are frontmatter primitives. The arrow aligns to the bottom. Native IME Send invokes the same validated action as the button. Do not add attachment, recording, tools or model controls.

### Navigation

A hamburger opens modal history; a compact Series 76/session title and new-conversation edit icon complete the header. Scrim, swipe and system Back dismiss history while retaining the conversation and draft. Selecting history resumes the backend session. New-chat/session switching is disabled during a pending send. Debug access appears only in the debug drawer; release source-set composables are no-ops.

### Cards / Containers

Outlined white product cards use 16dp padding, 10dp gaps and paired attribute/value columns. Preserve complete identifiers and source disclosure; source notes expand via a text action. User messages use neutral bubbles; assistant text remains unboxed. Error panels use the semantic wash with a recovery text action. The assistant Series 76 label identifies the speaker and is not a decorative eyebrow.

### Comparison

A reading surface with fixed labels, synchronized product scrolling, native text scaling and per-cell product/attribute accessibility context. Preserve the current dimensional strategy described in Layout. Source notes follow the table for each product; unavailable values stay explicit.

## Do's and Don'ts

### Do:
- **Do** preserve native scalable text, 48dp action targets, system/keyboard insets and meaningful vector-icon descriptions.
- **Do** keep the neutral tonal composer and compact left history drawer coherent with the approved conversation shell.
- **Do** retain full technical identifiers, units, N/A, source disclosure and expandable notes.
- **Do** preserve fixed comparison labels and synchronized product scrolling.
- **Do** distinguish UI fixture evidence from live model, backend and device verification.

### Don't:
- **Don't** restore the oversized Conversations dashboard or card-based history from historical composition C.
- **Don't** add decorative kickers, monograms, gradients, avatars, model selectors, voice, attachment controls or unrelated destinations.
- **Don't** put developer traces in release or inside customer product data.
- **Don't** replace semantic Compose content with screenshot backgrounds or rasterized text.
- **Don't** treat unimplemented dark/dynamic palettes, tablet layouts or physical-device behavior as verified capabilities.
