---
name: flutter-testing
description: Plans, writes, runs, and evaluates Flutter and Dart tests, including unit, widget, golden, integration, navigation, state-management, API, and MethodChannel tests. Use when adding Flutter test coverage, verifying a bug fix, or validating Flutter behavior.
---

# Flutter Testing

Test the visible and behavioral contract of a Flutter feature: input, state transition, rendered output, navigation, and side effect.

## Choose The Smallest Useful Test

- Unit test: mappers, validators, repositories with fakes, reducers, and pure business rules.
- State-management test: controller, Bloc/Cubit, Provider, Riverpod, or GetX state and effects.
- Widget test: screen state, semantics, user actions, loading, empty, and error rendering.
- Golden test: intentional visual regression coverage for stable UI.
- Integration test: navigation, plugins, permissions, storage, network boundaries, and real-device behavior.

## Workflow

1. State the expected behavior and reproduction scenario.
2. Add a failing test before a bug fix when practical.
3. Use deterministic fakes, clocks, streams, and dispatchers; avoid arbitrary delays.
4. Assert user-visible output and public state, not private implementation details.
5. Cover success, loading, empty, error, cancellation, and retry paths when relevant.
6. Run the narrowest test first, then `flutter test` or the relevant integration target.

## Widget And Integration Rules

- Use `pump`, `pumpAndSettle`, and explicit frame pumping deliberately; investigate animations that never settle.
- Find UI through text, semantics, keys, and accessible labels.
- Use stable keys only where semantic selectors are insufficient.
- Mock HTTP, storage, and MethodChannels at the boundary; test native bridges separately when needed.
- Pair golden or runtime screenshots with `runtime-ui-inspection` for defects that assertions cannot express.

## Completion

Record the exact commands, device/emulator context, and results used to verify a bug. Update Flutter indexes, symbol links, and bug-memory shards when changed tests expose new routes, states, calls, or regressions.
