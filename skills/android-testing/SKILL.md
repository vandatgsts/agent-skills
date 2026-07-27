---
name: android-testing
description: Plans, writes, runs, and evaluates Android Kotlin tests, including unit tests, coroutine and Flow tests, Room tests, ViewModel tests, Compose UI tests, and connected emulator/device tests. Use when adding test coverage, verifying a bug fix, or validating Android behavior.
---

# Android Testing

Test the observable contract of a feature: input, state transition, output, and side effect.

## Choose The Smallest Useful Test

- Unit test: pure mappers, commands, reducers, validation, and business rules.
- ViewModel/coroutine test: events, StateFlow, effects, repository interaction, and failure paths.
- Room test: DAO queries, migrations, and entity mapping.
- Compose UI test: rendered state, semantic labels, click behavior, and navigation callback.
- Connected test: device-specific behavior, permissions, rendering, and lifecycle integration.

## Workflow

1. Reproduce or specify the expected behavior first.
2. Test the failing behavior before applying a bug fix when practical.
3. Avoid timing sleeps; control coroutines, dispatchers, clocks, and fakes.
4. Assert visible state and important side effects, not internal implementation details.
5. Include success, empty, error, and cancellation/lifecycle boundaries when relevant.
6. Run the narrowest test first, then the relevant module or app task.

## Compose Rules

- Find nodes through semantics, text, role, or content description.
- Verify user-visible states rather than private composable implementation.
- Use stable test tags only where semantic selectors are insufficient.
- Pair screenshot/runtime inspection with tests for visual defects that assertions cannot express.

## Completion

Record exact commands and results for bug verification. Update bug-memory shards and symbol/index metadata when tests expose changed flows or symbols.
