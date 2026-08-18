---
name: manual-runtime-ui-testing
description: Perform interactive runtime UI testing on a currently running application. Use only when the user explicitly invokes `$manual-runtime-ui-testing`; never invoke implicitly or infer activation from a UI-related request. Allows proactive in-app navigation, taps, typing, scrolling, selecting target-app system dialogs, and scenario replay while capturing isolated UI evidence.
---

# Manual Runtime UI Testing

## Activation gate

Proceed only after an explicit `$manual-runtime-ui-testing` invocation in the current user message. Do not activate from natural-language requests alone.

## Scope

- Identify the target app, device/window, route, and test scenario.
- Interact freely within the target app to reproduce and verify UI flows: launch or relaunch it, tap, long-press, scroll, type non-sensitive test data, switch orientation, and follow target-app permission or picker dialogs.
- Capture fresh screenshots only of the target app surface in `.ai/ui-inspections/<timestamp>/`.
- Do not expose or retain notifications, credentials, personal content, or unrelated windows.
- Do not confirm irreversible actions such as purchases, account deletion, destructive data removal, or submissions to external services without separate user approval.

## Workflow

1. Confirm the target foreground surface and record resolution, orientation, theme, locale, font scale, and relevant state.
2. Drive the requested scenario end to end; do not stop at source-level reasoning.
3. Capture evidence before and after meaningful state transitions or suspected defects.
4. Inspect evidence for layout, accessibility, selected/loading/error states, navigation, and interaction defects.
5. Trace confirmed defects through project indexes and source. Update bug memory with screenshot evidence.
6. After a fix, repeat the identical scenario and capture the verification result.

## Report

For each finding, provide observed versus expected behavior, evidence path, route/symbol, reproduction steps, confidence, and next verification.
