---
name: runtime-ui-inspection
description: Captures a currently running app screen and inspects the rendered UI for visual or interaction defects. Use when diagnosing layout, clipping, overlap, wrong state, navigation, loading, empty, error, accessibility, or visual-regression bugs in Android, Flutter, web, or desktop apps.
---

# Runtime UI Inspection

Inspect the app as rendered, not only its source code. Capture evidence first, then connect observed defects to the relevant UI state, source paths, and symbols.

## Preconditions

- Confirm the target app, device/window, and scenario are currently running.
- Capture only the intended app surface. Do not include passwords, tokens, personal data, notifications, or unrelated windows in saved evidence.
- Prefer a fresh screenshot immediately after reproducing the reported state.
- Do not change product UI or dismiss data-loss dialogs unless the user asks.

## Capture Workflow

1. Reproduce the target state with the fewest necessary actions.
2. Capture one or more screenshots at the current resolution and orientation.
3. Save temporary evidence under `.ai/ui-inspections/<timestamp>/`; do not commit screenshots unless the user asks.
4. Record device/window size, orientation, theme, locale, font scale, and relevant app state when available.
5. Inspect the screenshot before opening broad source areas.

For Android, prefer an attached emulator/device screenshot command such as:

```powershell
adb exec-out screencap -p > .ai/ui-inspections/<timestamp>/screen.png
```

Use the platform's existing screenshot capability for web or desktop targets. If no capture path is available, ask the user to attach a screenshot rather than guessing from source code.

## Inspection Checklist

Check the captured UI for:

- clipped, truncated, overlapping, or off-screen content;
- incorrect padding, alignment, size, z-order, or safe-area handling;
- unreadable text, poor contrast, missing icons, or wrong assets;
- wrong loading, empty, error, selected, disabled, premium, or permission state;
- stale data after an action, duplicate content, or missing content;
- navigation destination, back behavior, dialog, sheet, keyboard, and system-bar issues;
- tap targets that are visually misleading or inaccessible;
- differences across orientation, density, theme, locale, or font scale.

Separate an observed visual defect from an inferred implementation cause. A screenshot proves appearance, not root cause.

## Trace To Code

After identifying a visible issue:

1. Search the relevant architecture and symbol indexes for the screen, route, composable/widget, state, and event.
2. Open only the affected UI/state source needed to explain the observation.
3. Trace the chain: user action → event → state update → rendered UI.
4. Check lifecycle, async loading, configuration, and navigation boundaries when the UI is stale or inconsistent.

For a confirmed defect, update bug memory using the bug shard workflow. Reference the screenshot path, affected symbols, reproduction steps, and verification scenario.

## Report Format

Report each finding with:

- observed result and expected result;
- screenshot evidence path and capture context;
- severity and user impact;
- exact reproduction steps;
- affected route/screen, source path, and symbol when known;
- confidence: observed, strongly inferred, or unconfirmed;
- recommended verification after a fix.

Example:

```markdown
### UI-001 — Bottom action is hidden behind system navigation

- Evidence: `.ai/ui-inspections/2026-07-27T161500/editor.png`
- Context: Android emulator, portrait, dark theme, editor route.
- Observed: The Save button is partially covered by the navigation bar.
- Expected: The full button remains tappable above system insets.
- Affected: `EditorScreen`, `Scaffold` bottom padding.
- Confidence: observed.
- Verify: Test portrait and landscape with gesture and three-button navigation.
```

## Verification

After a fix, repeat the same scenario and capture a new screenshot. Compare the result against the original evidence, then record the actual verification outcome. Do not mark a visual bug fixed solely because compilation succeeds.
