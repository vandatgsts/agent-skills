---
name: android-kotlin-native-indexing
description: Builds and incrementally maintains direct V4 Android Kotlin/Java architecture and symbol indexes for semantic lookup, lifecycle and callback tracing, and Flutter bridge analysis.
---

# Android/Kotlin direct V4 indexing

Use this skill with `symbol-indexing`. Read its V4 policy before initializing, updating, deleting, or validating index data.

The agent derives semantic records for each changed Kotlin or Java source. The engine verifies the source and writes source-owned shards directly; it never creates a whole-project intermediate index.

## Commands

```powershell
python <skill-dir>/scripts/index_android_v4.py <project-root> init
python <skill-dir>/scripts/index_android_v4.py <project-root> upsert --input <update.json>
python <skill-dir>/scripts/index_android_v4.py <project-root> delete-source --file <path>
python <skill-dir>/scripts/index_android_v4.py <project-root> lookup --qualified-name <name> --record
python <skill-dir>/scripts/index_android_v4.py <project-root> validate
```

An upsert is an authoritative replacement for every source in the update envelope. Include all current architecture and symbol records for that source, including an empty symbol array when appropriate. Use `delete-source` after removing a source file.

## Outputs

Maintain:

- `.ai/indexes/CODE_INDEX_ANDROID.md` for the human-readable architecture, modules, features, and flows.
- `.ai/indexes/codeindex_android.json` as the bounded architecture entry manifest.
- `.ai/indexes/android/` for source-owned architecture and named flow, feature, and bridge shards.
- `.ai/indexes/symbols/android_symbols.json` as the bounded symbol entry manifest.
- `.ai/indexes/symbols/android/` for source-owned symbol shards and deterministic source, symbol, and qualified-name routes.

The manifests declare layout, source scope, generation, and aggregate counts. They do not contain or enumerate the full index.

## Source scope

Index Kotlin and Java product code under `android/app/src/main`, `app/src/main`, and `modules/*/src/main`. Exclude build and generated output, IDE metadata, `R.java`, `BuildConfig.java`, and generated view binding.

## Architecture records

For every included source, record path, language, package, module, feature, layer, purpose, imports, classes, objects, interfaces, companion objects, important properties, related files, keywords, risks, and TODO/FIXME notes. Keep deep method metadata out of architecture records.

## Symbol records

Index Activities, Fragments, ViewModels, Services, Workers, receivers, managers, repositories, classes, objects, interfaces, lifecycle methods, suspend functions, properties, constants, callbacks, listeners, and platform handlers.

Every important symbol needs:

- name, qualified name, type, owner, signature, visibility, parameters, and return type
- exact start/end lines and async/suspend information
- callers, callees, state reads/writes, side effects, and related symbols/files
- lifecycle and thread/coroutine context
- searchable tags and risks
- relevant coroutine, Flow/StateFlow/SharedFlow, LiveData, injection, ads, billing, Firebase, storage, network, or image-processing metadata
- MethodChannel name, handled method, arguments, result behavior, native target, callbacks, and thread context when applicable

The engine assigns `symbol_id` and `shard_ref`. Relationship fields use qualified names and resolve through deterministic routes.

Classify symbols by module, feature, and semantic concern. Prefer lifecycle/UI, state, navigation, capture, detection, enhancement, duplicate review, permission, storage/data, API/network, ads, billing, Firebase, and platform bridge before using owner fallback.

## Flutter bridge tracing

Track:

```text
Flutter invokeMethod -> Android handler -> native manager/service -> callback/result -> Flutter state update
```

Record bidirectional references when both sides are known. Represent a cross-platform relationship with platform plus qualified name; do not copy full symbol metadata into the other platform index.

## Retrieval and maintenance

Search qualified-name routes, symbol routes, and owning symbol shards before opening complete source files. Follow architecture, flow, feature, and bridge records only as needed.

After code creation, modification, deletion, rename, move, API change, dependency change, lifecycle change, or MethodChannel change, upsert affected sources, update related callers/callees and named records, supply `summary_markdown` when architecture documentation changes, then run complete validation. Never leave stale hashes, line ranges, routes, flows, or bridge links.
