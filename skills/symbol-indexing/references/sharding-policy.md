# Direct V4 index policy

This policy is the storage and validation contract shared by Android and Flutter indexing.

## Core invariants

- Source code is the only bootstrap input. Do not create an aggregate architecture or symbol JSON as an intermediate artifact.
- One source update authoritatively replaces every architecture and symbol record owned by that source.
- Store each full symbol record exactly once.
- Use deterministic route buckets for lookup by source path, symbol ID, and qualified name.
- Keep platform entry manifests bounded; they declare layout and statistics rather than enumerating every shard.
- A complete index uses only V4 schemas. Reject any other schema instead of converting it.

## Entry manifests

Architecture manifests use `code-index-manifest-v4`. Symbol manifests use `code-symbol-manifest-v4`.

Each manifest records:

- platform and language
- generation and update time
- source scope
- directory layout and route-bucket strategy
- counts needed for integrity checks
- the path of its paired manifest

Android and Flutter use the same schemas while keeping their platform manifests and shard directories separate.

## Source-owned layout

The platform wrapper supplies the architecture and symbol roots. The engine writes:

```text
<architecture-root>/architecture/<module>/<feature>/<source-id>.json
<architecture-root>/flows/<record-id>.json
<architecture-root>/features/<record-id>.json
<architecture-root>/bridges/<record-id>.json
<symbol-root>/shards/<module>/<feature>/<concern>/<source-id>-<chunk>.json
<symbol-root>/routes/source/<bucket>.json
<symbol-root>/routes/symbol/<bucket>.json
<symbol-root>/routes/qualified/<bucket>.json
```

Symbols from one source may belong to several concern shards. When one source/concern group exceeds a hard limit, split only that group into numbered chunks.

## Update envelope

The `upsert` command accepts a JSON object with schema `code-index-update-v4`:

```json
{
  "schema": "code-index-update-v4",
  "project_metadata": {
    "project_name": "Example"
  },
  "summary_markdown": "# Example Code Index\n\nArchitecture summary.\n",
  "sources": [
    {
      "path": "app/src/main/java/example/MainActivity.kt",
      "architecture": {
        "layer": "presentation/activity",
        "purpose": "Application entry activity",
        "related_features": ["launcher"]
      },
      "symbols": [
        {
          "name": "onCreate",
          "qualified_name": "MainActivity.onCreate",
          "type": "lifecycle_method",
          "owner": "MainActivity",
          "signature": "override fun onCreate(savedInstanceState: Bundle?)",
          "start_line": 20,
          "end_line": 42,
          "calls": [],
          "called_by": [],
          "reads_state": [],
          "writes_state": [],
          "side_effects": [],
          "related_symbols": [],
          "related_files": [],
          "tags": [],
          "risks": []
        }
      ]
    }
  ],
  "delete_sources": [],
  "flows": [],
  "features": [],
  "bridges": [],
  "delete_flow_ids": [],
  "delete_feature_ids": [],
  "delete_bridge_ids": []
}
```

Every flow, feature, and bridge must have a stable `id`. Omitted arrays mean no change. A source included in `sources` is replaced even if its symbol array is empty.

`init` creates a minimal Markdown summary. Supply `summary_markdown` when architecture, feature, or flow documentation changes; the engine writes it in the same transaction as affected shards and manifests.

## Identity and routes

The engine derives `symbol_id` from platform, normalized source path, qualified name, and normalized signature. Line numbers are excluded from identity.

- Source routes record source hash, architecture shard, symbol shards, and owned symbol IDs.
- Symbol routes map `symbol_id` to qualified name, source, owning shard, and shard path.
- Qualified-name routes may contain multiple targets for overloaded or repeated names.
- Relationship fields store qualified names. Resolve them through routes at retrieval time so a moved symbol does not require rewriting unrelated shards.

## Scope

- `full`: every included product source must have one source route and architecture shard.
- `boundary`: index public entry points, callbacks, side effects, and threading contracts for external or rarely modified modules.
- `excluded`: generated output, build output, caches, samples, and unused external internals.

The manifest declares source globs and exclusions. Complete validation compares `full` scope routes with the source tree.

## Limits

Measure UTF-8 JSON serialized with two-space indentation and a trailing newline.

| File | Warning | Hard limit |
|---|---:|---:|
| Root manifest | 300 lines | 500 lines |
| Architecture, route, flow, feature, or bridge shard | 400 lines | 600 lines |
| Symbol shard | 800 lines or 15 symbols | 1,200 lines or 20 symbols |
| Any non-root shard | 40 KiB | 64 KiB |

A hard-limit violation fails the operation. Do not minify JSON to evade limits. A single record that cannot fit must be reduced or redesigned.

## Atomic updates

Stage every changed payload in a sibling temporary file. Write a transaction journal, replace data and route shards, replace entry manifests last, then delete unreferenced source-owned shards. On the next command, finish any journaled transaction before reading manifests.

Never delete paths outside the project root. Only delete shards explicitly owned by a source route or deterministic named-record path.

## Validation

Complete validation rejects:

- unsupported schemas or platform mismatches
- malformed UTF-8 and common mojibake sequences
- missing, duplicate, or mismatched source and symbol routes
- duplicate symbol IDs
- nonexistent source files or stale source hashes
- invalid and out-of-range line ranges
- missing or orphan architecture/symbol shards
- route targets that disagree with owning shards
- duplicate flow, feature, or bridge IDs
- incorrect manifest counts
- hard-limit violations
- missing product-source coverage for `full` scope

Ordinary upserts validate the changed records and touched route buckets. Run complete validation after moves, package changes, bulk generation, or changes to indexing rules.
