# Series 76 Technical Assistant

<!-- impeccable:product-schema 1 -->

## Platform

android

## Stack

Kotlin with Jetpack Compose and Material 3. FastAPI, LangChain and local PostgreSQL are mandatory assessment dependencies.

## Users

Plant engineers looking up Series 76 actuators and comparing candidates against technical requirements. Developers inspect real tool calls in a separate development-only screen.

## Product Purpose

Retrieve accurate technical data, recommend suitable products, and resume saved conversations with their context intact.

## Operating Context

Single-user assessment application, no authentication. Backend and PostgreSQL run locally; Android connects from an emulator or a device. No offline synchronization is required.

## Capabilities and Constraints

Exactly three screens: conversations, multi-turn chat, developer debug. The backend owns history and technical filtering. All numbers originate in series_76_electric_data.pdf. Preserve complete part numbers, units, service, frequency, unavailable states and notes. Tables compare multiple products inside chat. Every screen handles loading and errors.

## Brand Commitments

Latest redesign request: the user rejected the large index/cards as too basic, chose Gemini as the closer reference, and confirmed chat-first startup with conversation history in a left slide-out drawer. They approved the revised Gemini-style home/drawer mockups and their native adaptations. Preserve English and the Konecto lilac accent, neutral surfaces, compact header, typography-led greeting, two draft-only shortcut pills and a rounded tonal composer. The prior composition C is historical, not visual authority for this redesign. Native Android behavior and the assessment's existing functions remain binding. No additional business capabilities.

User approved an English interface, clear soft light surfaces, rounded cards inspired by supplied references 2 and 3, and the Konecto lilac palette (website primary #BD7BFF). Reference 1 informs typographic confidence only, not oversized overlapping text. No recording controls, search, login, voice, onboarding or unrelated features. Mockup-first workflow was explicitly chosen. Composition C (action in header) was approved through a structured user reply on 2026-11-03.

## Evidence on Hand

Assessment in docs/assessment-en.pdf. Validated OCR output in data/extracted/series76 and PostgreSQL catalogue queries in backend/catalog. Android is implemented and compiled in mobile/android, with Compose tests in an API35 emulator and unit/HTTP-contract tests. Real PostgreSQL history/products survived a backend/database restart with scripted language routing. OpenRouter model selection/configuration, real language evaluation and physical-device validation remain pending. Example conversation titles in mockups/screenshots are androidTest fixtures, never preloaded app sessions.

## Product Principles

- Accurate context-qualified numbers before decoration.
- One primary action per screen.
- End-user product information separated from developer internals.
- Implemented, compiled, integrated and verified are distinct states.

## Accessibility & Inclusion

Native Android navigation and system Back, scalable text, TalkBack semantics, readable contrast and touch targets of at least 48 dp.
