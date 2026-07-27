---
name: bug-memory-tracking
description: Records and retrieves durable project bug history: symptoms, evidence, root causes, fixes, verification, and regressions. Use when diagnosing a bug or crash, investigating a recurring issue, implementing a fix, reviewing a regression, or preserving debugging knowledge across sessions.
---

# Bug Memory Tracking

Maintain project-specific debugging knowledge so agents do not repeat failed investigations or fixes.

## Persistent Files

Maintain these files at the project root:

- `BUG_INDEX.md`: concise, human-readable history.
- `bugindex.json`: machine-readable records for lookup.

Create them only when the project needs its first bug record. Keep both files synchronized. Prefer incremental changes; do not rewrite unrelated records.

## Before Debugging

1. Read `bugindex.json` and search by symptom, error text, feature, file, symbol, and related bug ID.
2. Read matching entries in `BUG_INDEX.md`.
3. Read the relevant code and symbol indexes before opening broad source areas.
4. Reuse a verified cause or fix only when the current evidence matches.

Do not create a bug record for expected behavior, an unconfirmed idea, or a transient build-environment failure unless it affects the project reproducibly.

## Record Schema

Each bug must contain:

- `id`: stable sequential ID such as `BUG-0001`.
- `title`: short observable problem statement.
- `status`: one allowed status.
- `feature`: owning feature or module.
- `severity`: low, medium, high, or critical.
- `affected_files` and `affected_symbols`.
- `symptoms`, `logs`, and reproducible steps.
- `root_cause`: confirmed cause; leave empty while investigating.
- `fix`: implemented solution; leave empty before a fix.
- `verification_steps` and verification result.
- `regression_risk`, `related_bugs`, and dated notes.

Never place secrets, full access tokens, personal data, or raw production payloads in bug memory.

## Allowed Statuses

- `OPEN`: reported, not yet investigated.
- `INVESTIGATING`: evidence collection or root-cause analysis in progress.
- `FIXED`: fix implemented; verification remains incomplete.
- `VERIFIED`: fix passed defined verification.
- `WONT_FIX`: consciously accepted; include rationale.
- `REGRESSION`: a previously resolved issue has returned.

Use status transitions that reflect evidence. Do not mark a bug `FIXED` or `VERIFIED` merely because code was changed.

## Workflow

### Report

Create an `OPEN` record with the report, scope, evidence, and reproduction steps. Link suspected duplicates instead of creating duplicate records.

### Investigate

Change status to `INVESTIGATING`. Add observed behavior, narrowed scope, relevant files/symbols, failed hypotheses, and evidence. Keep unconfirmed theories in notes, not in `root_cause`.

### Fix

Record the confirmed root cause, exact fix, changed files/symbols, and regression risk. Change status to `FIXED` only after the change is implemented.

### Verify

Record commands, tests, device scenarios, or manual steps actually performed and their result. Change to `VERIFIED` only after they pass. If the issue returns, set `REGRESSION` and link the earlier record.

## Markdown Format

Use one concise section per bug:

```markdown
## BUG-0001 — Editor drag resets after rotation

- Status: VERIFIED
- Feature: editor
- Severity: high
- Affected: `EditorViewModel.onEvent`, `RoomCanvas`
- Symptoms: Dragged item returns to its pre-rotation position.
- Reproduce: Rotate an item, drag it, save, reopen the room.
- Root cause: Move command used stale rotation coordinates.
- Fix: Build the move command from the latest scene state.
- Verification: `:app:compileDebugKotlin`; manual rotate/drag/save/reopen scenario passed.
- Regression risk: Coordinate transforms and undo/redo.
- Related: BUG-0007
```

## JSON Format

Keep `bugindex.json` valid JSON with a top-level `bugs` array:

```json
{
  "bugs": [
    {
      "id": "BUG-0001",
      "title": "Editor drag resets after rotation",
      "status": "VERIFIED",
      "feature": "editor",
      "severity": "high",
      "affected_files": ["app/src/main/java/.../EditorViewModel.kt"],
      "affected_symbols": ["EditorViewModel.onEvent"],
      "symptoms": ["Dragged item returns to its pre-rotation position."],
      "logs": [],
      "reproduction_steps": ["Rotate an item", "Drag it", "Save and reopen the room"],
      "root_cause": "Move command used stale rotation coordinates.",
      "fix": "Build the move command from the latest scene state.",
      "fixed_files": ["app/src/main/java/.../EditorViewModel.kt"],
      "verification_steps": [":app:compileDebugKotlin", "Manual rotate/drag/save/reopen scenario"],
      "verification_result": "passed",
      "regression_risk": "Coordinate transforms and undo/redo.",
      "related_bugs": ["BUG-0007"],
      "notes": []
    }
  ]
}
```

## Maintenance Rules

- Update bug memory whenever a bug is reported, investigated, fixed, verified, reopened, or intentionally declined.
- Update linked code/symbol indexes when a fix changes symbols, flows, routes, or package paths.
- Search existing records before adding one; preserve IDs and history.
- Mention the bug ID, affected path, and symbol when reporting debugging results.
