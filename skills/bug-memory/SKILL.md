---
name: bug-memory-tracking
description: Records and retrieves durable project bug history using a 2-tier Hybrid Architecture (Project-level manifest/shards + Global-level prevention patterns). Use when diagnosing a bug or crash, investigating a recurring issue, implementing a fix, reviewing a regression, or preserving debugging knowledge across sessions.
---

# Bug Memory Tracking (Hybrid Architecture)

Maintain project-specific debugging knowledge and cross-project prevention patterns without bloating token context.

## 2-Tier Storage Layout (Mô hình Hybrid 2 tầng)

Tri thức xử lý và phòng ngừa lỗi được tổ chức 2 tầng:

1. **Tầng 1 - Project Level (`<project>/.ai/bugs/`)**: Chứa chi tiết thực thi cụ thể của từng dự án (manifest, shards, stacktraces, affected symbols, verification steps).
2. **Tầng 2 - Global Level (`~/.gemini/GLOBAL_BUG_PATTERNS.md`)**: Chứa các quy tắc vàng (Golden Rules) và Anti-patterns kinh điển được đúc kết từ thực tế để áp dụng phòng ngừa sớm cho mọi dự án.

```text
~/.gemini/GLOBAL_BUG_PATTERNS.md         # Tầng 2: Global Golden Prevention Rules & Anti-patterns
<project>/.ai/bugs/BUG_INDEX.md          # Tầng 1: short human-readable index with Global Pattern link
<project>/.ai/bugs/bugindex.json         # Tầng 1: bug-index-manifest-v2 with global_pattern field
<project>/.ai/bugs/<feature>/BUG-0001.json # Tầng 1: complete execution record for one bug
```

- `.ai/bugs/BUG_INDEX.md` lists ID, status, feature, global pattern, title, and shard path only.
- `.ai/bugs/bugindex.json` is the machine-readable manifest and contains lightweight lookup fields plus `shard` and `global_pattern`.
- Each shard contains complete evidence, root cause, fix, verification, regression risk, notes, and optional `global_pattern` link.

Use a lowercase kebab-case feature folder. Use `general` when the bug has no feature owner. Do not put full bug details back into the root manifest.

## Before Debugging (Pre-Fix Check)

1. Read Global Rules: Check `~/.gemini/GLOBAL_BUG_PATTERNS.md` to identify known architectural anti-patterns early (Lifecycle, Threading, CameraX, Billing, AdMob layout, System UI, etc.).
2. Search `.ai/bugs/bugindex.json` by symptom, error text, feature, file, symbol, global pattern, and related bug ID.
3. Open only matching `.ai/bugs/<feature>/BUG-<id>.json` shards.
4. Read matching `.ai/bugs/BUG_INDEX.md` entries and relevant code/symbol indexes.
5. Reuse a verified cause or fix only when current evidence matches.

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
- `global_pattern`: optional pattern ID (e.g., `PAT-LIFECYCLE-001`, `PAT-THREADING-001`) linking to global rules.
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

Record confirmed cause, exact fix, changed symbols, and actual verification in the shard. Update summary fields in `.ai/bugs/bugindex.json` and `.ai/bugs/BUG_INDEX.md`. Set `VERIFIED` only after defined checks pass.

### Pattern Promotion (Hybrid Rule)

Nếu nguyên nhân gốc và giải pháp mang tính quy luật kiến trúc chung hoặc có nguy cơ tái diễn ở các dự án khác, đúc kết một quy tắc vàng (Golden Rule) hoặc Anti-pattern mới bổ sung vào `~/.gemini/GLOBAL_BUG_PATTERNS.md` và gắn `global_pattern` tương ứng vào bug shard.

### Regression

Set the returning bug to `REGRESSION` or create a linked new shard when the cause differs. Keep both records and link IDs in `related_bugs`.

## Root Manifest Format

Keep `.ai/bugs/bugindex.json` valid JSON:

```json
{
  "schema": "bug-index-manifest-v2",
  "bugs": [
    {
      "id": "BUG-0001",
      "title": "Required access bottom sheet cannot be restored",
      "status": "VERIFIED",
      "feature": "permission",
      "severity": "high",
      "affected_symbols": [
        "RequiredAccessBottomSheet",
        "RequiredAccessBottomSheet.onResume"
      ],
      "shard": ".ai/bugs/permission/BUG-0001.json",
      "global_pattern": "PAT-LIFECYCLE-001"
    }
  ]
}
```

## Bug Shard Format

```json
{
  "id": "BUG-0001",
  "title": "Required access bottom sheet cannot be restored",
  "status": "VERIFIED",
  "feature": "permission",
  "severity": "high",
  "global_pattern": "PAT-LIFECYCLE-001",
  "affected_files": [
    "app/src/main/java/.../RequiredAccessBottomSheet.kt"
  ],
  "affected_symbols": [
    "RequiredAccessBottomSheet",
    "RequiredAccessBottomSheet.onResume"
  ],
  "symptoms": [
    "App crashes during startup with Fragment$InstantiationException: could not find Fragment constructor."
  ],
  "logs": [
    "Unable to instantiate fragment RequiredAccessBottomSheet"
  ],
  "reproduction_steps": [
    "Show RequiredAccessBottomSheet",
    "Recreate the activity or restore process",
    "Launch app"
  ],
  "root_cause": "RequiredAccessBottomSheet declared a required constructor parameter. FragmentManager restores fragments using a no-argument constructor.",
  "fix": "Removed constructor parameters and used FragmentResult with stable key.",
  "fixed_files": [
    "app/src/main/java/.../RequiredAccessBottomSheet.kt"
  ],
  "verification_steps": [
    ":app:compileDebugKotlin",
    "Process death and recreation test"
  ],
  "verification_result": "passed",
  "regression_risk": "Low. Relies on standard AndroidX FragmentResult APIs.",
  "related_bugs": [],
  "notes": []
}
```

## `.ai/bugs/BUG_INDEX.md` Format

Keep one short line per bug, grouped by status or feature:

```markdown
| ID | Status | Feature | Global Pattern | Title | Record |
| --- | --- | --- | --- | --- | --- |
| BUG-0001 | VERIFIED | permission | PAT-LIFECYCLE-001 | Required access bottom sheet cannot be restored | .ai/bugs/permission/BUG-0001.json |
```

## Maintenance Rules

- Update affected shard, `.ai/bugs/bugindex.json`, and `.ai/bugs/BUG_INDEX.md` whenever a bug changes state.
- Keep manifest `shard` paths valid after file or feature moves.
- Update linked code/symbol indexes when a fix changes symbols, flows, routes, or package paths.
- Search manifest and global patterns before adding a bug; preserve IDs and history.
- Mention bug ID, shard path, global pattern, and affected symbol in debugging results.
