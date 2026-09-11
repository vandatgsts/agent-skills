---
name: symbol-indexing
description: Builds and incrementally maintains direct V4 symbol indexes for Flutter/Dart and Android Kotlin/Java without an aggregate intermediate index. Use for fast symbol lookup, caller/callee tracing, state and side-effect analysis, routes, callbacks, and platform bridges.
---

# Direct V4 symbol indexing

Maintain symbol data as source-owned semantic shards. Never construct an aggregate symbol collection before writing shards.

Use this skill together with the platform skill:

- `flutter-code-indexing` for Dart and Flutter.
- `android-kotlin-native-indexing` for Kotlin and Java.

Read [references/sharding-policy.md](references/sharding-policy.md) before initializing, updating, deleting, or validating an index.

## Persistent entry points

- Flutter architecture manifest: `.ai/indexes/codeindex_flutter.json`
- Flutter symbol manifest: `.ai/indexes/symbols/flutter_symbols.json`
- Android architecture manifest: `.ai/indexes/codeindex_android.json`
- Android symbol manifest: `.ai/indexes/symbols/android_symbols.json`

The entry points contain bounded metadata and layout declarations only. Detailed records live in source-owned shards and deterministic route buckets.

## Update contract

Analyze each changed source file and submit one `code-index-update-v4` record. A source update is an authoritative replacement for that file: it replaces its architecture record, symbols, routes, and source hash together.

Use the platform wrapper:

```powershell
python <platform-skill>/scripts/index_<platform>_v4.py <project-root> upsert --input <update.json>
```

For a deleted source, use `delete-source`. Run `validate` after structural changes and before reporting index maintenance complete.

Use `lookup --qualified-name`, `lookup --symbol-id`, or `lookup --source`; add `--record` only when the owning data is needed.

## Symbols

Index important named code entities, including classes, methods, constructors, fields, state, routes, API calls, lifecycle methods, callbacks, services, repositories, managers, platform-channel calls, and constants.

Every symbol record must include:

- `name`, `qualified_name`, `type`, `file`, `owner`, and `signature`
- exact `start_line` and `end_line`
- `platform`, `language`, visibility, async/suspend information
- parameters and return type
- callers, callees, state reads/writes, and side effects
- related symbols/files, tags, risks, and platform-specific metadata

The engine assigns `symbol_id` and `shard_ref`. Do not generate either field manually.

## Retrieval

Search in this order:

1. Qualified-name route bucket.
2. Symbol route bucket.
3. Owning symbol shard.
4. Architecture, feature, flow, or bridge shard.
5. Source file only when the indexed metadata is insufficient or code must be edited.

Use source routes for reverse lookup and deletion. Resolve cross-platform references through qualified names and platform metadata instead of copying full symbol records.

## Maintenance invariant

Never finish a code change with stale source hashes, line ranges, routes, caller/callee links, or architecture references. Update only affected source-owned shards; a complete validation may scan all shards but ordinary writes must remain incremental.
