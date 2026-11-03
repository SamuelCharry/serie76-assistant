---
name: Konecto Series 76 Android
description: A quiet native technical conversation workspace in light and dark.
colors:
  light-primary: "#73617F"
  light-on-primary: "#FFFFFF"
  light-primary-container: "#F0EAF7"
  light-on-primary-container: "#675479"
  light-secondary: "#73617F"
  light-on-secondary: "#FFFFFF"
  light-secondary-container: "#F0EAF7"
  light-on-secondary-container: "#675479"
  light-tertiary: "#BD7BFF"
  light-on-tertiary: "#211A2B"
  light-background: "#FCFCFD"
  light-on-background: "#211A2B"
  light-surface: "#FFFFFF"
  light-on-surface: "#211A2B"
  light-surface-variant: "#F6F3F9"
  light-on-surface-variant: "#62596C"
  light-outline: "#94899E"
  light-outline-variant: "#E7E1EF"
  light-error: "#9E2036"
  light-error-container: "#FFE9ED"
  light-on-error-container: "#6E1324"
  dark-primary: "#D0BDE2"
  dark-on-primary: "#21182C"
  dark-primary-container: "#30263E"
  dark-on-primary-container: "#E1D1F0"
  dark-secondary: "#D0BDE2"
  dark-on-secondary: "#21182C"
  dark-secondary-container: "#30263E"
  dark-on-secondary-container: "#E1D1F0"
  dark-tertiary: "#BD7BFF"
  dark-on-tertiary: "#21182C"
  dark-background: "#101014"
  dark-on-background: "#F4F0F8"
  dark-surface: "#1B1921"
  dark-on-surface: "#F4F0F8"
  dark-surface-variant: "#24212B"
  dark-on-surface-variant: "#BFB4CB"
  dark-outline: "#95869F"
  dark-outline-variant: "#44394F"
  dark-error: "#FFB2BD"
  dark-error-container: "#42232D"
  dark-on-error-container: "#FFDCE2"
  light-soft-accent-1: "#F4ECFD"
  light-soft-accent-2: "#E5DCF3"
  dark-soft-accent-1: "#30273E"
  dark-soft-accent-2: "#433354"
typography:
  display:
    fontFamily: "Rethink Sans"
    fontSize: "38sp"
    fontWeight: 500
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
  field-composer-light:
    backgroundColor: "{colors.light-surface}"
    textColor: "{colors.light-on-surface}"
    rounded: "{rounded.composer}"
    padding: "16dp 10dp 10dp 20dp"
    typography: "{typography.body}"
  row-selected-light:
    backgroundColor: "{colors.light-primary-container}"
    textColor: "{colors.light-on-surface}"
    rounded: "{rounded.history}"
    padding: "14dp 12dp"
    typography: "{typography.title-small}"
  card-product-light:
    backgroundColor: "{colors.light-surface}"
    textColor: "{colors.light-on-surface}"
    rounded: "{rounded.card}"
    padding: "16dp"
    typography: "{typography.body-medium}"
  panel-error-light:
    backgroundColor: "{colors.light-error-container}"
    textColor: "{colors.light-on-error-container}"
    rounded: "{rounded.card}"
    padding: "16dp"
    typography: "{typography.body-medium}"
  bubble-user-light:
    backgroundColor: "{colors.light-surface-variant}"
    textColor: "{colors.light-on-surface}"
    rounded: "{rounded.message}"
    padding: "16dp"
    typography: "{typography.body}"
  button-text-light:
    textColor: "{colors.light-on-primary-container}"
    typography: "{typography.label}"
  field-composer-dark:
    backgroundColor: "{colors.dark-surface}"
    textColor: "{colors.dark-on-surface}"
    rounded: "{rounded.composer}"
    padding: "16dp 10dp 10dp 20dp"
    typography: "{typography.body}"
  row-selected-dark:
    backgroundColor: "{colors.dark-primary-container}"
    textColor: "{colors.dark-on-surface}"
    rounded: "{rounded.history}"
    padding: "14dp 12dp"
    typography: "{typography.title-small}"
  card-product-dark:
    backgroundColor: "{colors.dark-surface}"
    textColor: "{colors.dark-on-surface}"
    rounded: "{rounded.card}"
    padding: "16dp"
    typography: "{typography.body-medium}"
  panel-error-dark:
    backgroundColor: "{colors.dark-error-container}"
    textColor: "{colors.dark-on-error-container}"
    rounded: "{rounded.card}"
    padding: "16dp"
    typography: "{typography.body-medium}"
  bubble-user-dark:
    backgroundColor: "{colors.dark-surface-variant}"
    textColor: "{colors.dark-on-surface}"
    rounded: "{rounded.message}"
    padding: "16dp"
    typography: "{typography.body}"
  button-text-dark:
    textColor: "{colors.dark-on-primary-container}"
    typography: "{typography.label}"
---

# Design System: Konecto Series 76 Android

## Overview

**Creative North Star: "The Engineering Journal"**

A quiet native conversation workspace with an open center, soft violet controls and locally bundled Rethink Sans. Near-white light surfaces and graphite dark surfaces keep technical reading clear. A static diffuse light field and sourced Konecto wave give the empty chat atmosphere without placing geometry behind the results.

This refresh records the implemented V4 refinement of the retained editorial components. The scope is English Android phone UI in both light and dark modes: chat, left conversation history and development-only debug. Geometry uses dp and text uses sp. UI fixtures demonstrate presentation, not model quality, backend integration or physical-device performance.

**Key Characteristics:**
- Centered Hello and icon-only empty-chat toolbar.
- Soft gradient actions, outlined composer and restrained static background.
- Matched light/dark semantic roles with a saved native appearance switch.
- Complete technical evidence in readable cards and synchronized comparison columns.

## Colors

The frontmatter records the explicit light/dark Material roles and soft-action stops from Theme.kt. Each prefixed token maps to its same-named Compose role; primary and secondary share values. Unlisted Material roles retain library defaults.

### Primary
- **Quiet Violet:** `light-primary` and `dark-primary` supply native action roles; `on-primary` is their corresponding content role.
- **Selection:** `primary-container` supplies selected history; `on-primary-container` supplies composer cursor, soft-action content, recovery links and progress.
- **Soft Accent:** the two scheme-specific stops form the horizontal gradient used by New chat and Send. This is a deliberate native control material.

### Secondary
- **Konecto Lilac:** both `tertiary` roles retain the identity accent. It is not the general body-text color.

### Neutral
- **Canvas and Reading Surface:** `background` and `surface` support the chat/drawer and composer/data containers; `on-background` and `on-surface` supply reading contrast.
- **Quiet Surface and Muted Ink:** `surface-variant` supports user bubbles and comparison labels; `on-surface-variant` supplies dates, disclosure and placeholders.
- **Outline and Fine Rule:** `outline` supports native outlined controls; `outline-variant` supplies composer/card borders and dividers.
- **Semantic Error:** `error`, `error-container` and `on-error-container` distinguish unavailable values and recovery panels in each scheme.

**The Content First Rule.** Show the sourced wave only on the empty, idle chat; remove its geometry while typing, sending or reading messages.

## Typography

**Display and Body Font:** locally bundled Rethink Sans, regular/medium/semibold, licensed in mobile/android/FONT-LICENSE.txt. Native monospace remains reserved for selectable debug JSON.

### Hierarchy
- **Display:** Hello uses the display metrics with medium weight and tightened tracking. The theme's underlying displaySmall remains semibold; the component override is the visible greeting.
- **Headline:** retained medium heading role; not the greeting.
- **Title large:** conversation heading and active session title.
- **Title medium:** product identifiers, comparison and empty-history headings.
- **Title small:** saved history titles and Recent label.
- **Body:** messages, composer and waiting label.
- **Body medium:** attributes, recovery and loading text.
- **Body small:** dates, source disclosure and comparison guidance.
- **Label:** native actions and the functional Assistant speaker label.

The theme also defines headlineLarge, labelMedium and labelSmall; they are not promoted as new surface patterns. Hello and Thinking expose stable whole-text accessibility semantics rather than individual animated letters.

**The Context Stays Visible Rule.** Preserve complete technical identifiers, units, unavailable states and source notes; retain native font scaling rather than shrinking data to fit.

## Layout

Chat fills the phone window. Empty-chat toolbar contains menu and new-conversation icons with no title; existing conversations show the session title. Hello is centered inside the content area between the app bar and composer and hides for keyboard, loading, errors or pending requests. No shortcut rows or footer interrupt this space.

The composer is anchored using navigation-bar and IME insets, 16dp horizontal/12dp vertical outer padding and an 8dp gap. The field grows from two to five lines; Send is 48dp. Chat content uses 20dp horizontal/16dp vertical padding and 24dp message gaps. User bubbles align right with a 320dp maximum width; assistant prose remains unboxed.

The modal drawer occupies 84% of the parent width with 20dp internal horizontal padding. History uses 6dp row gaps, two-line ellipsized titles and dates. The Dark theme switch has a 56dp minimum row height. Android system appearance is used until the user makes an explicit selection; the Boolean choice persists in local SharedPreferences. Status/navigation icon appearance follows the effective scheme.

Comparison fixes specification labels while product columns share horizontal scrolling. At fontScale 1, label/product widths are 148/216dp and header/row heights are 96/76dp; these multiply by fontScale clamped to at least 1. No tablet breakpoint is established.

## Elevation & Depth

Custom surfaces use tonal separation and thin rules without custom shadows. Native Material state layers and modal behavior remain. The drawer scrim uses onSurface at 24% alpha. Borders and gradients are native materials of this world.

The static background has two radial light fields. Their empty-chat alphas are 0.85/0.8 in light and 0.6/0.8 in dark; both reduce to 0.25 when content appears. Only the empty idle canvas carries the original 184-path Konecto vector, tinted muted violet at 0.32 light/0.24 dark alpha, cropped into a 320dp-high lower region with a -38dp offset. The native conversion and source hash are recorded in .impeccable/references/konecto-wave-origin.json. No shipping raster is used.

**The Native Feedback Rule.** Retain native press, drawer and list feedback; make custom text motion static when Android animations are disabled.

Hello reveals per-letter tint, opacity and baseline over 640ms with cubic-bezier(0.22,1,0.36,1), beginning visibly at 35% opacity. Thinking uses a 1500ms linear color wave only during an actual pending send. Both observe live Android animator-scale changes and become static when disabled. The native drawer and list placement retain native motion; debug uses a 180ms crossfade. A waiting label does not claim access to model internals.

## Shapes

Fine boundaries pair with rounded native surfaces. Theme small/medium/large corners are 12/16/24dp. History, soft New chat, product/error cards, user bubbles and composer use the frontmatter radii. Send is circular. The drawer rounds its trailing corners only. Composer and technical cards use 1dp borders. Native text/outlined buttons and switches retain their own shape and state behavior.

## Components

### Buttons

New chat is a full-width soft-gradient action with scheme-specific onPrimaryContainer text/vector content, a 52dp minimum height and 14dp corners. Send uses the same gradient in a 48dp circle. Its icon uses onPrimaryContainer when enabled and onSurfaceVariant at 40% alpha when disabled; the gradient remains. Send is disabled for blank draft, sending, unresolved history or reconciliation. Native press/focus feedback remains authoritative. Text actions use onPrimaryContainer where explicitly supplied; other native controls inherit the theme.

### Inputs / Fields

The outlined composer uses the active surface and onSurface body text, a muted placeholder, subtle outlineVariant border and onPrimaryContainer cursor. The field has no floating label; its arrow aligns to the bottom. IME Send calls the same action. The border does not currently change on focus; text cursor, selection and native semantics supply feedback.

### Navigation

Menu opens left modal history; the edit vector creates a conversation. Scrim, swipe and system Back dismiss history while retaining chat/draft. Selected history uses primaryContainer. Session switching and New chat disable while sending. The Dark theme row toggles the local appearance choice. Debug entry and response inspection remain development-only; release source-set composables are no-ops.

### Cards / Containers

Outlined product cards use surface/onSurface, paired attribute/value columns, 16dp padding and 10dp gaps. Source notes expand through a text action. Assistant is a functional speaker label, not an ornamental eyebrow. User messages use surfaceVariant bubbles; error panels use semantic containers and recovery actions. Loading feedback appears only for pending operations.

### Comparison

Fixed specification labels, synchronized product scrolling, scalable cells and per-cell accessibility context support technical reading. Complete identifiers, units, unavailable values and source notes remain explicit.

### Icons and Background

Conversation controls use native fine-stroke vectors, meaningful content descriptions and at least 48dp touch controls. The sourced Konecto wave is background-only, has a null content description and contains no logo, copy or web controls. It is not a replacement for semantic Compose UI.

## Do's and Don'ts

### Do:
- Do preserve scalable text, 48dp action targets, meaningful icon descriptions and system/keyboard insets.
- Do use scheme-specific content roles for readable controls, messages, history and data surfaces.
- Do retain full identifiers, units, N/A, source disclosure and expandable notes.
- Do preserve fixed comparison labels and synchronized product scrolling.
- Do keep the sourced wave decorative and static, with its provenance alongside the native vector.

### Don't:
- Don't restore shortcut rows, a slogan, redundant branding labels or the superseded two-line greeting.
- Don't use saturated purple slabs, decorative kickers, hard offset shadows or system display faces.
- Don't put wave geometry behind populated chat or animate the background at idle.
- Don't add voice, attachments, model selectors, search or unrelated controls.
- Don't place developer traces in release product data or replace semantic content with rasterized text.
