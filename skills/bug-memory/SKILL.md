---
name: bug-memory-tracking
description: Records and retrieves durable project bug history using a root manifest and per-bug shards. Use when diagnosing a bug or crash, investigating a recurring issue, implementing a fix, reviewing a regression, or preserving debugging knowledge across sessions.
---

# Bug Memory Tracking

Maintain project-specific debugging knowledge without growing one large bug file.

## Storage Layout

Use this layout once a project has bug memory:

```text
.ai/bugs/BUG_INDEX.md                # short human-readable index
bugindex.json                        # bug-index-manifest-v2
.ai/bugs/<feature>/BUG-0001.json     # complete record for one bug
```

- `.ai/bugs/BUG_INDEX.md` lists ID, status, feature, title, and shard path only.
- `bugindex.json` is the machine-readable manifest and contains the same lightweight lookup fields plus `shard`.
- Each shard contains the complete evidence, root cause, fix, verification, and notes for exactly one bug.

Use a lowercase kebab-case feature folder. Use `general` when the bug has no feature owner. Do not put full bug details back into the root manifest.

Create the root manifest and first shard only when the project has its first reproducible bug. When migrating an existing flat `bugindex.json`, preserve IDs, create one shard per record, reduce the root to the manifest, and update `.ai/bugs/BUG_INDEX.md` in the same change.

## Before Debugging

1. Search `bugindex.json` by symptom, error text, feature, file, symbol, and related bug ID.
2. Open only the matching `.ai/bugs/<feature>/BUG-<id>.json` shards.
3. Read matching `.ai/bugs/BUG_INDEX.md` entries and relevant code/symbol indexes.
4. Reuse a verified cause or fix only when current evidence matches.

Do not record expected behavior, an unconfirmed idea, or a transient environment failure unless it affects the project reproducibly.

## Allowed Statuses

- `OPEN`: reported, not yet investigated.
- `INVESTIGATING`: evidence collection or root-cause analysis in progress.
- `FIXED`: fix implemented; verification remains incomplete.
- `VERIFIED`: fix passed defined verification.
- `WONT_FIX`: consciously accepted; include rationale.
- `REGRESSION`: a previously resolved issue has returned.

Do not mark a bug `FIXED` or `VERIFIED` merely because code was changed.

## Bug Shard Schema

Every bug shard must contain:

- `id`, `title`, `status`, `feature`, and `severity`.
- `affected_files` and `affected_symbols`.
- `symptoms`, `logs`, and `reproduction_steps`.
- `root_cause`: confirmed cause only; leave empty while investigating.
- `fix`, `fixed_files`, and `verification_steps`.
- `verification_result`, `regression_risk`, `related_bugs`, and dated `notes`.

Never store secrets, full access tokens, personal data, or raw production payloads.

## Workflow

### Report

Create a new `OPEN` shard and add its lightweight entry to both root indexes. Link suspected duplicates instead of creating duplicate records.

### Investigate

Update only that shard with observed behavior, narrowed scope, relevant files/symbols, failed hypotheses, and evidence. Keep unconfirmed theories in notes, not in `root_cause`. Update the manifest status.

### Fix and Verify

Record the confirmed cause, exact fix, changed symbols, and actual verification in the shard. Update the summary fields in `bugindex.json` and `.ai/bugs/BUG_INDEX.md`. Set `VERIFIED` only after the defined checks pass.

### Regression

Set the returning bug to `REGRESSION` or create a linked new shard when the cause differs. Keep both records and link IDs in `related_bugs`.

## Root Manifest Format

Keep `bugindex.json` valid JSON:

```json
{
  "schema": "bug-index-manifest-v2",
  "bugs": [
    {
      "id": "BUG-0001",
      "title": "Editor drag resets after rotation",
      "status": "VERIFIED",
      "feature": "editor",
      "severity": "high",
      "affected_symbols": ["EditorViewModel.onEvent"],
      "shard": ".ai/bugs/editor/BUG-0001.json"
    }
  ]
}
```

## Bug Shard Format

```json
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
```

## `.ai/bugs/BUG_INDEX.md` Format

Keep one short line per bug, grouped by status or feature:

```markdown
| ID | Status | Feature | Title | Record |
| --- | --- | --- | --- | --- |
| BUG-0001 | VERIFIED | editor | Editor drag resets after rotation | `.ai/bugs/editor/BUG-0001.json` |
```

## Maintenance Rules

- Update the affected shard, root manifest, and `.ai/bugs/BUG_INDEX.md` whenever a bug changes state.
- Keep manifest `shard` paths valid after file or feature moves.
- Update linked code/symbol indexes when a fix changes symbols, flows, routes, or package paths.
- Search the manifest before adding a bug; preserve IDs and history.
- Mention bug ID, shard path, affected path, and symbol in debugging results.
