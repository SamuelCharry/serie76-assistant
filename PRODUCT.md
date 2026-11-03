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

Current refinement: centered Hello with a gentle letter entrance, animated waiting text only while sending, no shortcut rows/slogan/redundant Series76 labels. Both light and dark modes are explicitly requested; a local drawer switch saves the choice. Use only Konecto's sourced wave background language, with diffuse light and readable native content. Prior Editorial A and V2 home compositions are historical for the user-replaced parts. See docs/MOBILE_DIRECTION_V4.md.

Current redesign: the user rejected the generic V2 finish, retained chat-first startup and left history, and approved Editorial A across the whole app with native adaptations. Use locally bundled Rethink Sans, Konecto white/plum/lilac, an editorial two-line actuator greeting, ruled text shortcut rows, outlined white composer and coherent fine-stroke icons. Native drawer, restrained entrance and press motion; no added business features. V2/C are historical, not current visual authority.

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
