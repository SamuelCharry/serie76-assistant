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
  login-heading:
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
  label-medium:
    fontFamily: "Rethink Sans"
    fontSize: "12sp"
    fontWeight: 500
    lineHeight: "16sp"
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
  profile-avatar: "50%"
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
  profile-footer-light:
    backgroundColor: "{colors.light-background}"
    textColor: "{colors.light-on-background}"
    rounded: "{rounded.history}"
    padding: "14dp 4dp"
    typography: "{typography.title-small}"
  profile-avatar-light:
    textColor: "{colors.light-on-primary-container}"
    rounded: "{rounded.profile-avatar}"
    size: "40dp"
  profile-menu-light:
    backgroundColor: "{colors.light-surface}"
    textColor: "{colors.light-on-surface}"
    rounded: "{rounded.card}"
  profile-editor-light:
    backgroundColor: "{colors.light-surface}"
    textColor: "{colors.light-on-surface}"
    rounded: "{rounded.composer}"
  profile-appearance-heading-light:
    textColor: "{colors.light-on-surface-variant}"
    typography: "{typography.label-medium}"
    padding: "12dp 16dp"
  profile-footer-dark:
    backgroundColor: "{colors.dark-background}"
    textColor: "{colors.dark-on-background}"
    rounded: "{rounded.history}"
    padding: "14dp 4dp"
    typography: "{typography.title-small}"
  profile-avatar-dark:
    textColor: "{colors.dark-on-primary-container}"
    rounded: "{rounded.profile-avatar}"
    size: "40dp"
  profile-menu-dark:
    backgroundColor: "{colors.dark-surface}"
    textColor: "{colors.dark-on-surface}"
    rounded: "{rounded.card}"
  profile-editor-dark:
    backgroundColor: "{colors.dark-surface}"
    textColor: "{colors.dark-on-surface}"
    rounded: "{rounded.composer}"
  profile-appearance-heading-dark:
    textColor: "{colors.dark-on-surface-variant}"
    typography: "{typography.label-medium}"
    padding: "12dp 16dp"
  button-sign-in-light:
    backgroundColor: "{colors.light-primary}"
    textColor: "{colors.light-on-primary}"
    rounded: "{rounded.card}"
    typography: "{typography.label}"
  login-heading-light:
    textColor: "{colors.light-on-background}"
    typography: "{typography.login-heading}"
  button-sign-in-dark:
    backgroundColor: "{colors.dark-primary}"
    textColor: "{colors.dark-on-primary}"
    rounded: "{rounded.card}"
    typography: "{typography.label}"
  login-heading-dark:
    textColor: "{colors.dark-on-background}"
    typography: "{typography.login-heading}"
---

# Design System: Konecto Series 76 Android

## Overview

**Creative North Star: "The Engineering Journal"**

A quiet native conversation workspace with an open center, soft violet controls and locally bundled Rethink Sans. Near-white light surfaces and graphite dark surfaces keep technical reading clear. A diffuse light field, gently drifting sourced Konecto wave and twelve quiet motes give the empty chat atmosphere without placing geometry behind the results.

This record retains the approved editorial system and bounded empty-chat ambient motion, with a native sign-in form and server-backed profile. The scope is English Android phone UI in both light and dark modes: sign-in, chat, left conversation history with a compact profile footer/menu, and development-only debug. Geometry uses dp and text uses sp. UI fixtures demonstrate presentation, not model quality or physical-device performance; authentication integration evidence is recorded separately from visual fixtures.

**Key Characteristics:**
- Centered Hello and icon-only empty-chat toolbar.
- Soft gradient actions, outlined composer and restrained empty-chat ambient motion.
- Matched light/dark semantic roles with saved Light/Dark/System appearance choices.
- Unboxed native sign-in and an explicit server-backed profile state.
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

**The Content First Rule.** Show the sourced wave and motes only on the visible, empty, idle chat; remove them while typing, sending, loading history, showing a history error, opening history or reading messages.

## Typography

**Display and Body Font:** locally bundled Rethink Sans, regular/medium/semibold, licensed in mobile/android/FONT-LICENSE.txt. Native monospace remains reserved for selectable debug JSON.

### Hierarchy
- **Display:** Hello uses the display metrics with medium weight and tightened tracking. The theme's underlying displaySmall remains semibold; the component override is the visible greeting.
- **Login heading:** Welcome back uses the existing theme displaySmall semibold metrics; the separate role records its weight without changing Hello.
- **Headline:** retained medium heading role; not the greeting.
- **Title large:** conversation heading and active session title.
- **Title medium:** product identifiers, comparison and empty-history headings.
- **Title small:** saved history titles and Recent label.
- **Body:** messages, composer and waiting label.
- **Body medium:** attributes, recovery and loading text.
- **Body small:** dates, source disclosure and comparison guidance.
- **Label:** native actions and the functional Assistant speaker label.

The profile Appearance heading uses the label-medium role. The theme also defines headlineLarge and labelSmall; they are not promoted as new surface patterns. Hello and Thinking expose stable whole-text accessibility semantics rather than individual animated letters.

**The Context Stays Visible Rule.** Preserve complete technical identifiers, units, unavailable states and source notes; retain native font scaling rather than shrinking data to fit.

## Layout

Chat fills the phone window. Empty-chat toolbar contains menu and new-conversation icons with no title; existing conversations show the session title. Hello is centered inside the content area between the app bar and composer and hides for keyboard, loading, errors or pending requests. No shortcut rows or footer interrupt this space.

The composer is anchored using navigation-bar and IME insets, 16dp horizontal/12dp vertical outer padding and an 8dp gap. The field grows from two to five lines; Send is 48dp. Chat content uses 20dp horizontal/16dp vertical padding and 24dp message gaps. User bubbles align right with a 320dp maximum width; assistant prose remains unboxed.

The modal drawer occupies 84% of the parent width with 20dp internal horizontal padding. History uses 6dp row gaps, two-line ellipsized titles and dates. A profile footer stays below the scrolling history and a half-alpha outlineVariant divider. Its compact anchored menu is constrained to 240 to 300dp width. Light, Dark and System replace the previous binary switch; System follows Android appearance and is the initial choice. The selected mode persists in local SharedPreferences; an existing Boolean preference restores Light or Dark until a mode is selected. Status/navigation icon appearance follows the effective scheme.

Sign-in uses an unboxed form centered in the available window, a 420dp maximum width, 28dp horizontal/32dp vertical outer padding and 20dp vertical gaps. Safe-drawing and IME insets plus vertical scrolling keep the form reachable with keyboard or enlarged text. It uses the quiet diffuse field without wave geometry or motes.

Comparison fixes specification labels while product columns share horizontal scrolling. At fontScale 1, label/product widths are 148/216dp and header/row heights are 96/76dp; these multiply by fontScale clamped to at least 1. No tablet breakpoint is established.

## Elevation & Depth

Custom surfaces use tonal separation and thin rules without custom shadows. Native Material state layers, popup shadows and modal behavior remain. The profile menu explicitly uses surface with zero tonal elevation; the retained legacy-only editor explicitly uses surface rather than a tinted container. The current sign-in form adds no card, raised slab or custom shadow. The drawer scrim uses onSurface at 24% alpha. Borders and gradients are native materials of this world.

The background retains two static radial light fields. Their empty-chat alphas are 0.85/0.8 in light and 0.6/0.8 in dark; both reduce to 0.25 when content appears. Only the empty idle canvas carries the original 184-path Konecto vector, tinted muted violet at 0.32 light/0.24 dark alpha, cropped into a 320dp-high lower region with a -38dp offset. The native conversion and source hash are recorded in .impeccable/references/konecto-wave-origin.json. No shipping raster is used.

**The Native Feedback Rule.** Retain native press, drawer and list feedback; make custom text and ambient motion static when Android animations are disabled.

Ambient motion uses twelve deterministic violet motes in the same lower 320dp region as the wave. Their radii repeat 1.1/1.45/1.8dp; each follows a smooth 10dp horizontal/14dp vertical orbit over 32 seconds, with 0.30 light/0.38 dark alpha. The wave layer drifts from -3 to +3dp horizontally and -4 to 0dp vertically. The light fields, text and composer do not join this drift. No particle physics, per-frame randomness, connecting lines or blur is introduced.

The ambient clock updates at most once every 50ms (20 updates/second), and phase is read only during Canvas drawing or graphicsLayer updates. It runs only while the screen is RESUMED and the chat is visible, empty and idle: no messages, nonblank draft, keyboard, pending send, history loading or history error; opening history removes the decoration. Android animator-scale zero and battery saver pause the clock, observed while mounted. Pausing retains a still phase and resuming does not catch up elapsed background time; disposal cancels the clock. This bounded work is an implementation policy, not a measured energy or physical-device smoothness claim.

Hello reveals per-letter tint, opacity and baseline over 640ms with cubic-bezier(0.22,1,0.36,1), beginning visibly at 35% opacity. Thinking uses a 1500ms linear color wave only during an actual pending send. Both observe live Android animator-scale changes and become static when disabled. The native drawer and list placement retain native motion; debug uses a 180ms crossfade. A waiting label does not claim access to model internals.

## Shapes

Fine boundaries pair with rounded native surfaces. Theme small/medium/large corners are 12/16/24dp. History, soft New chat, product/error cards, user bubbles and composer use the frontmatter radii. Send is circular. The drawer rounds its trailing corners only. Composer and technical cards use 1dp borders. The profile avatar is circular, its menu uses the card radius and the retained legacy-only editor uses the composer radius. Sign in uses the card radius. Native text/outlined buttons, text fields and radio controls retain their shape and state behavior.

## Components

### Buttons

New chat is a full-width soft-gradient action with scheme-specific onPrimaryContainer text/vector content, a 52dp minimum height and 14dp corners. Send uses the same gradient in a 48dp circle. Its icon uses onPrimaryContainer when enabled and onSurfaceVariant at 40% alpha when disabled; the gradient remains. Send is disabled for blank draft, sending, unresolved history or reconciliation. Native press/focus feedback remains authoritative. Text actions use onPrimaryContainer where explicitly supplied; other native controls inherit the theme.

### Inputs / Fields

The outlined composer uses the active surface and onSurface body text, a muted placeholder, subtle outlineVariant border and onPrimaryContainer cursor. The field has no floating label; its arrow aligns to the bottom. IME Send calls the same action. The border does not currently change on focus; text cursor, selection and native semantics supply feedback.

### Navigation

Menu opens left modal history; the edit vector creates a conversation. Scrim, swipe and system Back dismiss history while retaining chat/draft. Selected history uses primaryContainer. Session switching and New chat disable while sending. The profile footer opens the authenticated profile and appearance menu. Sign out returns to sign-in after revocation; changing account uses a subsequent sign-in. Debug entry and response inspection remain development-only; release source-set composables are no-ops.

### Sign-in

A native form leads directly to the existing workspace without a new card family. Welcome back uses login-heading; supporting text uses body and onSurfaceVariant. The Email and Password fields are single-line native outlined fields with visible labels, email/password keyboards and disabled state while busy. Password starts masked, has a functional Show/Hide action and is cleared from the field at submission. IME Done and Sign in invoke the same action. Sign in has the card radius and a 52dp minimum height; its enabled primary/onPrimary treatment and native disabled/focus/press states remain Material-owned.

Checking your session shows a native linear progress indicator and body-medium status instead of credential fields. Invalid credentials, throttling and connection failures use explicit body-medium error text in the error role. Signing in changes the button label and disables repeated submission; a failed saved-session check can offer Retry saved session. No workspace history is shown before the server validates identity. No registration, password recovery or promotional controls are implied.

### Authenticated Profile and Appearance

The footer reuses background, the history radius, 14dp vertical/4dp horizontal padding and a 12dp avatar/text gap. The 40dp circular avatar retains Soft Accent and a 20dp fine-stroke profile vector in onPrimaryContainer, without an invented photograph or initials. Server-provided name and email use title-small and muted body-small, with a 2dp gap and one-line ellipsis.

The surface menu retains the card radius, native popup dismissal and 48dp native menu actions. Its header uses 16dp horizontal/12dp vertical padding, 4dp gaps, title-medium name (up to two lines), wrapping muted body-medium email and body-small Signed in status. Sign out replaces local identity editing; while busy its label becomes Signing out and the action disables. Failure stays visible in the error role and retains the account for retry, rather than claiming a successful exit. A different account signs in after sign-out; there is no inert switch-account control.

Light, Dark and System remain native selectable rows with trailing radios and selected semantics. Choosing appearance persists the local mode and closes the menu without changing the conversation or draft. Outside tap and system Back use native dismissal. The old local profile/editor remains only as a source fallback for isolated legacy presentation; its retained editor tokens do not authorize editing authenticated identity or treating local preferences as a server account.

Production uses FLAG_SECURE for sensitive windows. Visual evidence may remove it only in a test instance with declared fixtures; previews and screenshots never establish a real signed-in identity or expose credentials.

### Cards / Containers

Outlined product cards use surface/onSurface, paired attribute/value columns, 16dp padding and 10dp gaps. Source notes expand through a text action. Assistant is a functional speaker label, not an ornamental eyebrow. User messages use surfaceVariant bubbles; error panels use semantic containers and recovery actions. Loading feedback appears only for pending operations.

### Comparison

Fixed specification labels, synchronized product scrolling, scalable cells and per-cell accessibility context support technical reading. Complete identifiers, units, unavailable values and source notes remain explicit.

### Icons and Background

Conversation controls use native fine-stroke vectors, meaningful content descriptions and at least 48dp touch controls. The sourced Konecto wave and Canvas motes are decorative background-only content; the wave has a null content description and contains no logo, copy or web controls. It is not a replacement for semantic Compose UI.

## Do's and Don'ts

### Do:
- Do preserve scalable text, 48dp action targets, meaningful icon descriptions and system/keyboard insets.
- Do use scheme-specific content roles for readable controls, messages, history and data surfaces.
- Do show server-provided identity and explicit sign-in/sign-out states, and retain Light/Dark/System through native selectable rows.
- Do retain full identifiers, units, N/A, source disclosure and expandable notes.
- Do preserve fixed comparison labels and synchronized product scrolling.
- Do keep the sourced wave decorative with its provenance alongside the native vector; gate its bounded drift and motes by chat visibility, lifecycle, reduced motion and battery saver.

### Don't:
- Don't restore shortcut rows, a slogan, redundant branding labels or the superseded two-line greeting.
- Don't use saturated purple slabs, decorative kickers, hard offset shadows or system display faces.
- Don't put wave geometry or motes behind populated or busy chat, or run ambient motion while inactive, reduced motion is enabled or battery saver is active.
- Don't add voice, attachments, model selectors, search or unrelated controls.
- Don't invent a signed-in identity, edit authenticated identity through the legacy local form or show a nonfunctional account-switch action.
- Don't place developer traces in release product data or replace semantic content with rasterized text.
