---
name: Konecto Series 76 Android
description: An editorial actuator research workspace with native conversation history.
colors:
  primary: "#412C64"
  accent: "#BD7BFF"
  selection: "#EEE3FC"
  background: "#FCFCFD"
  surface: "#FFFFFF"
  ink: "#211A2B"
  quiet-surface: "#F6F3F9"
  muted-ink: "#62596C"
  outline: "#8A7E98"
  rule: "#D0ACE5"
  error: "#9E2036"
  error-wash: "#FFE9ED"
  error-ink: "#6E1324"
typography:
  display:
    fontFamily: "Rethink Sans"
    fontSize: "38sp"
    fontWeight: 600
    lineHeight: "42sp"
    letterSpacing: "-0.8sp"
  headline:
    fontFamily: "Rethink Sans"
    fontSize: "24sp"
    fontWeight: 500
    lineHeight: "30sp"
    letterSpacing: "0sp"
  title-large:
    fontFamily: "Rethink Sans"
    fontSize: "22sp"
    fontWeight: 500
    lineHeight: "28sp"
    letterSpacing: "0sp"
  title-medium:
    fontFamily: "Rethink Sans"
    fontSize: "18sp"
    fontWeight: 600
    lineHeight: "24sp"
    letterSpacing: "0sp"
  title-small:
    fontFamily: "Rethink Sans"
    fontSize: "15sp"
    fontWeight: 500
    lineHeight: "22sp"
    letterSpacing: "0sp"
  body:
    fontFamily: "Rethink Sans"
    fontSize: "16sp"
    fontWeight: 400
    lineHeight: "24sp"
    letterSpacing: "0sp"
  body-medium:
    fontFamily: "Rethink Sans"
    fontSize: "14sp"
    fontWeight: 400
    lineHeight: "21sp"
    letterSpacing: "0sp"
  body-small:
    fontFamily: "Rethink Sans"
    fontSize: "12sp"
    fontWeight: 400
    lineHeight: "18sp"
    letterSpacing: "0sp"
  label:
    fontFamily: "Rethink Sans"
    fontSize: "14sp"
    fontWeight: 500
    lineHeight: "20sp"
    letterSpacing: "0sp"
rounded:
  shortcut: "4dp"
  history: "12dp"
  action: "14dp"
  card: "16dp"
  message: "20dp"
  composer: "24dp"
spacing:
  "4": "4dp"
  "6": "6dp"
  "8": "8dp"
  "10": "10dp"
  "12": "12dp"
  "14": "14dp"
  "16": "16dp"
  "18": "18dp"
  "20": "20dp"
  "24": "24dp"
  "28": "28dp"
  "48": "48dp"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.action}"
    padding: "14dp 18dp"
    height: "52dp"
    typography: "{typography.label}"
  button-send:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    size: "48dp"
  button-text:
    textColor: "{colors.primary}"
    typography: "{typography.label}"
  button-outlined:
    textColor: "{colors.primary}"
    typography: "{typography.label}"
  field-composer:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.composer}"
    padding: "16dp 10dp 10dp 20dp"
    typography: "{typography.body}"
  row-shortcut:
    backgroundColor: "{colors.background}"
    textColor: "{colors.ink}"
    rounded: "{rounded.shortcut}"
    padding: "18dp 4dp"
    typography: "{typography.title-large}"
  row-selected:
    backgroundColor: "{colors.selection}"
    textColor: "{colors.ink}"
    rounded: "{rounded.history}"
    padding: "14dp 12dp"
    typography: "{typography.title-small}"
  card-product:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.card}"
    padding: "16dp"
  panel-error:
    backgroundColor: "{colors.error-wash}"
    textColor: "{colors.error-ink}"
    rounded: "{rounded.card}"
    padding: "16dp"
  bubble-user:
    backgroundColor: "{colors.quiet-surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.message}"
    padding: "16dp"
---

# Design System: Konecto Series 76 Android

## Overview

**Creative North Star: "The Engineering Journal"**

A contemporary engineering journal translated into native Android conversation controls. Near-white space, plum ink, fine lilac rules and locally bundled Rethink Sans establish a clear reading hierarchy. The interface leads with the question and gives technical results room to retain their context.

This records the user-approved Editorial A replacement of V2 as implemented in Kotlin and Jetpack Compose. The scope is light-mode phones, English UI and existing chat, history and development-only debug navigation. Native units remain dp for geometry and sp for text. Screenshot fixtures demonstrate presentation, not a real model or physical-device result.

**Key Characteristics:**
- Open editorial composition with ruled shortcuts and an outlined white composer.
- Regular, medium and semibold Rethink Sans with restrained plum emphasis.
- Compact native navigation, fine-stroke vectors and quiet motion.
- Complete technical evidence in readable cards and synchronized comparison columns.

## Colors

A near-white reading canvas gives plum actions and fine lilac rules their contrast. The frontmatter records explicit reused theme roles; unlisted Material roles remain library defaults.

### Primary
- **Konecto Plum** (`primary`): primary and secondary Material action color, greeting emphasis, send fill, cursor and progress indicator.
- **Selection Wash** (`selection`): primary/secondary containers and selected conversation background, with plum content.

### Secondary
- **Konecto Lilac** (`accent`): the explicit tertiary identity role; the current main surfaces do not use it for body text.
- **Lilac Rule** (`rule`): outlined composer, technical card boundaries, header and shortcut dividers.

### Neutral
- **Near White** (`background`): chat, drawer and app-bar canvas.
- **Reading White** (`surface`) and **Plum Ink** (`ink`): reading surfaces and high-priority text.
- **Quiet Surface** (`quiet-surface`): user messages and comparison label column.
- **Muted Ink** (`muted-ink`): dates, support text, source disclosure and placeholder.
- **Quiet Outline** (`outline`): native outlined-control boundaries.
- **Error**, **Error Wash** and **Error Ink** (`error`, `error-wash`, `error-ink`): missing catalogue values and recovery panels.

**The The Plum Action Rule.** Use plum for readable small actions and the enabled send control; lilac carries identity and fine structural accents.

## Typography

**Display and Body Font:** locally bundled Rethink Sans, regular/medium/semibold; font resources ship under Android res/font and the OFL license is recorded in mobile/android/FONT-LICENSE.txt. Native monospace is reserved for selectable debug JSON. Material role metrics are explicitly overridden in Theme.kt.

### Hierarchy
- **Display:** two-line greeting with semibold plum second line and slightly tightened tracking.
- **Headline:** medium drawer section heading.
- **Title large:** compact identity and shortcut titles; shortcuts override medium to semibold.
- **Title medium:** product identifiers, comparison and empty-history heading.
- **Title small:** history titles and Recent label.
- **Body:** messages, composer and greeting support.
- **Body medium:** attributes, shortcut support, recovery and loading text.
- **Body small:** dates, product caption, disclosure and debug JSON metrics.
- **Label:** assistant speaker label, native buttons and text actions.

The theme additionally declares headlineLarge, labelMedium and labelSmall; these are not promoted to the reusable ramp because the sampled screens do not explicitly use them.

**The The Context Stays Visible Rule.** Preserve complete technical identifiers, units, unavailable states and source notes; retain native font scaling rather than shrinking data to fit.

## Layout

Chat fills the phone window beneath a native compact app bar and its inset rule. Main content has 20dp horizontal and 16dp vertical padding with 24dp message gaps. The empty greeting starts at 17% of the available content height, clamped to 24?100dp, with an additional 4dp horizontal inset. Its support line is followed by 48dp space before two full-width ruled shortcut rows. Shortcuts populate and focus the draft without submitting. The greeting hides when the keyboard is visible.

The anchored composer area uses 16dp horizontal and 12dp vertical padding, navigation-bar and IME insets, and 8dp between elements. The field grows from two to five lines; its send target is 48dp. User bubbles align right with a 320dp maximum width; assistant prose is unboxed.

The drawer occupies 84% of the parent width with 20dp internal horizontal padding. It separates identity, new chat, history and footer with rules and deliberate spacing. History rows have 6dp gaps, two-line ellipsized titles and a date. Empty history is plain content rather than a decorative panel.

Comparison keeps labels fixed while product columns share a horizontal scroll. At fontScale 1 the label/product widths are 148/216dp and header/row heights are 96/76dp; dimensions multiply by fontScale clamped to at least 1. These are the implemented native dimensions, not a claim of arbitrary text-fit coverage. No responsive tablet breakpoint or dark palette is implemented.

## Elevation & Depth

Custom surfaces use white, restrained tonal separation and thin rules, without custom shadows. Native Material components retain their own state layers and modal behavior. The drawer uses an ink scrim at 24% alpha; native modal separation is part of the system rather than a violation of flat composition.

**The The Native Feedback Rule.** Retain native interaction feedback, modal separation and Android animation scaling; do not add perpetual animation.

Welcome text enters over 480ms with cubic-bezier(0.22, 1, 0.36, 1), starting at 86% opacity and about 5dp below its resting position; the rule grows from 86% width. Content is visible on the first frame. Shortcut arrows shift 3dp right/up on press over 140ms. History uses native animateItem placement, the drawer uses native motion, and debug changes surface through a 180ms crossfade. No hand-coded animation-scale override exists.

## Shapes

Fine rules pair with gently rounded interactive surfaces. The theme supplies small/medium/large corners of 12/16/24dp. Component-specific frontmatter records the smaller shortcut radius, history corners, new-chat action, user message, product card and composer. The drawer rounds only its trailing corners. Send is circular; native text and outlined buttons preserve native shape and state behavior. Technical cards and the composer use a 1dp border. Borders are a native material of this world and must not be banned.

## Components

### Buttons

The full-width plum New chat action has white content, a 52dp minimum height, edit vector and directional arrow. The send circle uses the same plum and white at 48dp. It disables for blank drafts, sending, unresolved history or reconciliation. Its disabled fill uses plum at 55% alpha with white icon; this state is a subdued action, not a separate primitive. Text actions use plum; the debug response selector is a native outlined button. Native press/focus semantics remain authoritative.

### Inputs / Fields

The white composer has a fine lilac outline, generous internal padding and no floating label. BasicTextField uses body type, a muted placeholder and plum cursor. The arrow aligns to its bottom. IME Send calls the same send action. Do not add unrelated accessory controls. The outline does not currently change on focus; native text cursor/selection and semantics supply feedback.

### Navigation

A hamburger opens the left modal history; identity/session title and a new-conversation edit vector complete the ruled header. Scrim, swipe and system Back dismiss history while retaining chat/draft. Selected history has a lilac wash. New-chat/session switching disables while sending. The separated footer links to debug only in debug builds; release source-set composables are no-ops.

### Ruled shortcuts

Text rows use semibold title, smaller muted subtitle, 24dp fine-stroke diagonal arrow and lilac separators. The whole row is actionable with a native 48dp minimum content height. Reuse this ruled text grammar rather than tonal action pills.

### Cards / Containers

White outlined product cards use paired attribute/value columns, 16dp padding and 10dp gaps. Source notes expand via a text action. Assistant identity is a functional speaker label, not an ornamental eyebrow. User messages use quiet-surface bubbles; error panels use semantic error wash, body text and recovery action. Progress appears only while a real operation is pending.

### Comparison

Fixed specification labels, synchronized product scrolling, scaled cells and per-cell accessibility context support technical reading. Source notes follow each product. Complete identifiers, units and unavailable values stay explicit.

### Icons

Production conversation controls use native vectors with round caps/joins and approximately 1.4?2 unit strokes in a 24-unit viewport. No icon font or text glyph substitutes. No shipping raster UI assets are used. The debug-only filled back arrow is an existing native exception, not the icon style to reproduce across new screens.

## Do's and Don'ts

### Do:
- **Do** preserve native scalable text, 48dp action targets, system/keyboard insets and meaningful icon descriptions.
- **Do** use the outlined white composer and ruled text shortcuts established by the editorial world.
- **Do** retain full technical identifiers, units, N/A, source disclosure and expandable notes.
- **Do** preserve fixed comparison labels and synchronized product scrolling.
- **Do** distinguish UI fixture evidence from live model, backend and device verification.

### Don't:
- **Don't** restore the historical tonal composer or oversized history dashboard.
- **Don't** add decorative kickers, gradients, ornamental imagery, hard offset shadows or system display faces.
- **Don't** introduce voice, attachments, model selectors, search or unrelated controls.
- **Don't** put developer traces in release or inside customer product data.
- **Don't** replace semantic Compose content with screenshot backgrounds or rasterized text.

Not canonized: the debug-only filled back arrow remains a visual exception; inherited Material role defaults are not additional brand tokens. Fixed-height comparison cells are an implementation constraint, not evidence of universal large-text fit. These were recorded rather than silently repaired during documentation.
