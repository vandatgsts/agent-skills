---
name: android-compose-ui
description: Designs, implements, reviews, and refactors Android Jetpack Compose UI. Use when creating or changing composables, screens, navigation UI, UI state rendering, responsive layouts, Material components, accessibility, or visual states in a Kotlin Android app.
---

# Android Compose UI

Build UI from explicit state and events. Keep composables focused on rendering; keep repository, coroutine, and mutation logic in ViewModels or domain layers.

## Before Editing

1. Read the relevant Android index and symbol entries.
2. Identify the route, screen, UI state, events, and ViewModel owner.
3. Define loading, content, empty, error, selected, and disabled states affected by the change.
4. Preserve the project theme, navigation, and existing architectural boundaries.

## Implementation Rules

- Use immutable UI state and state hoisting for reusable composables.
- Pass data and callbacks down; do not let leaf UI call repositories directly.
- Give list items stable keys and keep expensive work outside composition.
- Use `remember` only for UI-local state; derive values with `derivedStateOf` when appropriate.
- Handle system bars, IME, display cutouts, and content padding explicitly.
- Provide content descriptions for meaningful images and icons; keep tap targets usable.
- Prefer existing design tokens, typography, colors, and components over one-off styling.
- Keep navigation decisions at the screen/route boundary unless the project convention differs.

## Verification

1. Compile the affected variant.
2. Run relevant Compose/UI tests when available.
3. Use `runtime-ui-inspection` on a running app for layout, state, and interaction changes.
4. Update indexes when composables, routes, state, or events change.
