---
name: debugging-and-error-recovery
description: Diagnoses and fixes Android, Flutter, and general application failures through evidence-driven reproduction, localization, minimal repair, and regression verification. Use when a build fails, app crashes, behavior regresses, a callback is missing, state is wrong, or an error log needs root-cause analysis.
---

# Debugging And Error Recovery

Diagnose from evidence. Do not treat a plausible explanation as the root cause.

## Workflow

1. Read bug-memory manifest and matching shards first.
2. Capture the error, stack trace, screenshot, device state, and exact reproduction steps.
3. Classify the failure: build, startup, lifecycle, state, data, navigation, rendering, network, or platform integration.
4. Search indexes and symbols to localize the responsible flow.
5. Form a small number of falsifiable hypotheses and test the cheapest one first.
6. Apply the smallest fix that removes the confirmed cause.
7. Verify the original scenario plus the nearest regression boundary.

## Evidence Rules

- Preserve the original error text and relevant line numbers.
- Distinguish observed facts, inferred cause, and unconfirmed hypothesis.
- Check caller/callee chains, coroutine context, lifecycle ownership, and state writes for async failures.
- Use `runtime-ui-inspection` when the failure is rendered or interaction-visible.
- Do not suppress exceptions, add arbitrary delays, or broaden catch blocks merely to hide symptoms.

## Completion

Update the relevant bug shard with cause, fix, verification, and regression risk. Update code and symbol indexes if paths, symbols, flows, or package ownership changed.
