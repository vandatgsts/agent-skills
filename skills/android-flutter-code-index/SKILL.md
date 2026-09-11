---
name: flutter-code-indexing
description: Builds and incrementally maintains direct V4 Flutter/Dart architecture and symbol indexes for semantic lookup, state and navigation tracing, API flows, and native bridge analysis.
---

# Flutter/Dart direct V4 indexing

Use this skill with `symbol-indexing`. Read its V4 policy before initializing, updating, deleting, or validating index data.

The agent derives semantic records for each changed Dart source. The engine verifies the source and writes source-owned shards directly; it never creates a whole-project intermediate index.

## Commands

```powershell
python <skill-dir>/scripts/index_flutter_v4.py <project-root> init
python <skill-dir>/scripts/index_flutter_v4.py <project-root> upsert --input <update.json>
python <skill-dir>/scripts/index_flutter_v4.py <project-root> delete-source --file <path/to/file.dart>
python <skill-dir>/scripts/index_flutter_v4.py <project-root> lookup --qualified-name <name> --record
python <skill-dir>/scripts/index_flutter_v4.py <project-root> validate
```

An upsert is an authoritative replacement for every source in the update envelope. Include all current architecture and symbol records for that source, including an empty symbol array when appropriate. Use `delete-source` after removing a source file.

## Outputs

Maintain:

- `.ai/indexes/CODE_INDEX_FLUTTER.md` for the human-readable architecture, routes, features, and flows.
- `.ai/indexes/codeindex_flutter.json` as the bounded architecture entry manifest.
- `.ai/indexes/flutter/` for source-owned architecture and named flow, feature, and bridge shards.
- `.ai/indexes/symbols/flutter_symbols.json` as the bounded symbol entry manifest.
- `.ai/indexes/symbols/flutter/` for source-owned symbol shards and deterministic source, symbol, and qualified-name routes.

The manifests declare layout, source scope, generation, and aggregate counts. They do not contain or enumerate the full index.

## Source scope

Index product Dart code under `lib/`. Exclude build output, `.dart_tool`, IDE metadata, generated Dart files, platform build directories, and dependency/vendor trees unless the project explicitly treats them as product code.

## Architecture records

For every included source, record path, language, module, feature, layer, purpose, imports/exports, classes, mixins, extensions, enums, entry points, routes, related files, keywords, risks, and TODO/FIXME notes. Keep deep function metadata out of architecture records.

## Symbol records

Index widgets, screens, pages, controllers, bindings, middleware, services, repositories, managers, models, DTOs, mappers, enums, constants, constructors, methods, callbacks, and top-level functions.

Every important symbol needs:

- name, qualified name, type, owner, signature, visibility, parameters, and return type
- exact start/end lines and async information
- callers, callees, state reads/writes, side effects, and related symbols/files
- routes, navigation actions, API calls, storage actions, callbacks, and platform-channel calls
- searchable tags and risks

Detect Flutter and common state/navigation patterns including `StatelessWidget`, `StatefulWidget`, `State<T>`, GetX controllers/bindings, named routes, `Get.to*`, `Obx`, `GetBuilder`, `StreamBuilder`, `FutureBuilder`, lifecycle hooks, workers, editing/scroll/animation controllers, `MethodChannel`, and `EventChannel`.

The engine assigns `symbol_id` and `shard_ref`. Relationship fields use qualified names and resolve through deterministic routes.

Classify symbols by module, feature, and semantic concern. Prefer lifecycle/UI, state, navigation, input/picking, generation/processing, preview, result, permission, storage/data, API/network, ads, billing, and platform bridge before using owner fallback.

## Native bridge tracing

Track:

```text
Flutter caller -> MethodChannel/EventChannel -> native handler -> native target -> callback/result -> Flutter state update
```

Record bidirectional references when both sides are known. Represent a cross-platform relationship with platform plus qualified name; do not copy full native symbol metadata into the Flutter index.

## Retrieval and maintenance

Search qualified-name routes, symbol routes, and owning symbol shards before opening complete source files. Follow architecture, flow, feature, and bridge records only as needed.

After Dart creation, modification, deletion, rename, move, route change, API change, state change, or platform-channel change, upsert affected sources, update related callers/callees and named records, supply `summary_markdown` when architecture documentation changes, then run complete validation. Never leave stale hashes, line ranges, routes, flows, or bridge links.
