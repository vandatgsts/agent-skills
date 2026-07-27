---
name: code-review-and-quality
description: Reviews code changes for correctness, architecture, lifecycle safety, test coverage, maintainability, performance, and security. Use before committing, merging, releasing, or approving changes in Android, Flutter, or general application projects.
---

# Code Review And Quality

Review the changed behavior and its boundaries, not formatting alone.

## Review Sequence

1. Read the diff and identify the intended user-visible outcome.
2. Trace changed symbols through callers, state, navigation, storage, and side effects.
3. Check tests, build output, and runtime evidence proportionate to risk.
4. Report findings by severity with file path, symbol, evidence, impact, and recommendation.

## Quality Checks

- Correctness: null, empty, error, retry, cancellation, and concurrency paths.
- Architecture: UI/domain/data boundaries, dependency direction, and duplicate logic.
- Android: lifecycle ownership, coroutine dispatcher, Flow collection, Room migration, Compose recomposition, and configuration changes.
- UX: loading/error/empty states, accessibility, system insets, and navigation/back behavior.
- Reliability: cleanup, resource ownership, idempotency, and recoverable failure handling.
- Performance: unnecessary recomposition, main-thread I/O, large allocations, and repeated work.
- Security: secrets, logging of sensitive data, validation, permission scope, and unsafe file/network handling.

## Outcome

Separate blocking defects from suggestions. Do not claim approval without evidence from the relevant build, test, or runtime check. Record confirmed regressions in bug-memory.
