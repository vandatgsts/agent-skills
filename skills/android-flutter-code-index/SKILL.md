---
name: flutter-code-indexing
description: Creates architecture-level Flutter/Dart code indexes and maintains Flutter symbol indexes for function-level lookup. Use when working with large Flutter codebases, tracing feature flows, debugging controllers/routes/API calls, reducing token usage, or understanding architecture without rereading entire files.
---

# FLUTTER / DART CODE INDEXING SKILL

## GLOBAL V3 SHARDING POLICY

Always activate `symbol-indexing` with this skill and apply its `references/sharding-policy.md` contract when creating, migrating, rebalancing, or validating indexes.

Read legacy monolithic and v2 indexes, but emit `flutter-index-manifest-v3` and `flutter-symbol-manifest-v3` on `--rebalance`. V3 separates architecture, flows, features, symbols, and symbol routes so one screen or controller cannot force an entire feature into one oversized JSON file.

Partition Flutter symbols by module, feature, then concern. Prefer these concerns when detected: lifecycle/UI, state, navigation, input/picking, generation/processing, preview, result, permission, storage/data, API/network, ads, billing, and platform bridge. Use owner-based fallback only after semantic detection. Allow methods from one Widget, State, Controller, or ViewModel to live in different concern shards.

Enforce the global limits: root manifests at most 500 lines; architecture/flow/feature shards at most 600 lines; symbol shards at most 1,200 lines, 20 symbols, and 64 KiB. Treat a hard-limit violation as failure. Preserve full metadata only in the owning symbol shard and connect other shards with stable `symbol_ref`, `shard_ref`, and `depends_on` links.

You are a Flutter/Dart Codebase Indexing Agent.

Your responsibility is to maintain two separate retrieval layers:

1. `.ai/indexes/codeindex_flutter.json`
   - architecture
   - modules
   - features
   - flows
   - file relationships
   - important files

2. `.ai/indexes/symbols/flutter_symbols.json`
   - classes
   - methods/functions
   - routes
   - state variables
   - caller/callee relationships
   - line ranges
   - API calls
   - navigation actions
   - MethodChannel calls

The goal is to make Flutter code easy to query without rereading entire source files, while avoiding duplicated data between code indexes and symbol indexes.

---

# OUTPUT FILES

Maintain these entry files:

- `.ai/indexes/CODE_INDEX_FLUTTER.md`
- `.ai/indexes/codeindex_flutter.json`
- `.ai/indexes/symbols/flutter_symbols.json`

When `.ai/indexes/codeindex_flutter.json` uses a v2 or v3 manifest schema, treat it as an entry point. Follow every declared shard reference.

- `.ai/indexes/flutter/<shard>.json` for architecture/file data
- `.ai/indexes/flutter/flows/<shard>.json` for flow data in v3
- `.ai/indexes/flutter/features/<shard>.json` for feature data in v3
- `.ai/indexes/symbols/flutter/<shard>.json` for detailed symbols
- `.ai/indexes/symbols/flutter/routes/<shard>.json` for symbol routes in v3
- `.ai/indexes/symbols/flutter_symbols.json` as the symbol manifest

Never flatten a v2 or v3 manifest into a legacy monolithic index. After Dart additions, moves, renames, route changes, or refactors, update affected content, then run:

```powershell
python <skill-dir>/scripts/shard_flutter_indexes.py <project-root> --rebalance
python <skill-dir>/scripts/shard_flutter_indexes.py <project-root> --validate
```

The Flutter sharder partitions symbols by semantic concern and may place symbols from one source file into different shards. It must not split one symbol record or duplicate its full metadata.

When a project already has a v2 or v3 manifest, `--rebalance` must load all declared shards, rebuild the shard set, update both manifests, and remove stale generated shard files before `--validate` is run.

`--validate` must check manifest/shard integrity, hard limits, architecture/symbol coverage, source paths, line ranges, explicit cross-shard links, counts, and UTF-8. Compare declared product-code coverage with the source tree after structural refactors.

Do not generate shallow indexes.

Do not duplicate full function-level details inside `.ai/indexes/codeindex_flutter.json`.

Function-level details must live in:

- `.ai/indexes/symbols/flutter_symbols.json`

---

# SCAN SCOPE

Analyze:

- `lib/**/*.dart`
- Dart widgets
- screens/pages
- controllers
- GetX controllers
- GetX bindings
- routes
- middleware
- services
- repositories
- managers
- models
- DTOs
- mappers
- API layer
- local storage
- state management
- MethodChannel calls to native Android/iOS

Ignore:

- `build/`
- `.dart_tool/`
- generated files
- `*.g.dart`
- `*.freezed.dart`
- `*.gr.dart`
- `.idea/`
- `.vscode/`
- `android/build/`
- `ios/Pods/`

---

# CODE INDEX RESPONSIBILITY

`.ai/indexes/codeindex_flutter.json` is the macro-level architecture index.

It should contain:

- project overview
- architecture summary
- modules
- entry points
- routes
- method channels
- feature flows
- file responsibilities
- important files
- related files
- risks
- dead code
- duplicate logic

It should NOT contain detailed method/function metadata such as:

- full function signatures
- start/end line for every function
- caller/callee graph
- state reads/writes
- API calls per function
- navigation actions per function
- side effects per function

Those belong in:

- `.ai/indexes/symbols/flutter_symbols.json`

---

# REQUIRED FILE INDEX

For every important Dart file, collect only file-level and architecture-level information:

- path
- language
- layer
- purpose
- imports
- exports
- classes
- mixins
- extensions
- enums
- top-level symbols
- main_symbols
- related_features
- related_files
- keywords
- risks
- TODO/FIXME notes

Use `main_symbols` to reference symbols stored in:

- `.ai/indexes/symbols/flutter_symbols.json`

---

# FLUTTER-SPECIFIC DETECTION

Detect and index at macro level:

- StatelessWidget
- StatefulWidget
- State<T>
- GetxController
- GetView
- GetWidget
- Bindings
- Middleware
- Routes
- Named routes
- Get.to / Get.off / Get.offAll / Get.toNamed
- Rx variables
- Obx usage
- GetBuilder usage
- StreamBuilder / FutureBuilder
- initState
- dispose
- onInit
- onReady
- onClose
- workers: ever, once, debounce, interval
- TextEditingController
- ScrollController
- AnimationController
- MethodChannel.invokeMethod
- EventChannel
- platform channel constants

Detailed symbol information for these items must be stored in:

- `.ai/indexes/symbols/flutter_symbols.json`

---

# FLOW MAPPING

Detect and map Flutter flows:

- splash flow
- onboarding flow
- login/auth flow
- image picking flow
- image generation flow
- preview flow
- result flow
- payment/premium flow
- ads trigger flow from Flutter side
- API request flow
- navigation flow
- MethodChannel bridge flow

Represent flow steps as lightweight references to symbols.

Example:

```json
{
  "name": "Image Generation Flow",
  "steps": [
    {
      "file": "lib/presentation/view/screen/preview/preview_controller.dart",
      "symbol": "PreviewController.startGeneration",
      "action": "Starts image generation and navigates to result screen"
    }
  ]
}
```

Line ranges and caller/callee details must be stored in:

- `.ai/indexes/symbols/flutter_symbols.json`

---

# REQUIRED JSON STRUCTURE

`.ai/indexes/codeindex_flutter.json` must follow this structure:

```json
{
  "project_name": "",
  "platform": "flutter",
  "language": "dart",
  "architecture": "",
  "state_management": "",
  "routing": "",
  "modules": [],
  "entry_points": [],
  "routes": [],
  "method_channels": [],
  "flows": [],
  "features": [],
  "files": [
    {
      "path": "",
      "language": "dart",
      "layer": "",
      "purpose": "",
      "imports": [],
      "exports": [],
      "classes": [],
      "mixins": [],
      "extensions": [],
      "enums": [],
      "top_level_symbols": [],
      "main_symbols": [],
      "related_features": [],
      "related_files": [],
      "keywords": [],
      "risks": []
    }
  ],
  "important_files": [],
  "risks": [],
  "dead_code": [],
  "duplicate_logic": []
}
```

`main_symbols` should reference symbols stored in:

- `.ai/indexes/symbols/flutter_symbols.json`

Do not store detailed function bodies, caller/callee graphs, line ranges, or side effects inside `.ai/indexes/codeindex_flutter.json`.

---

# EXAMPLE CODE INDEX FILE ENTRY

```json
{
  "path": "lib/presentation/view/screen/preview/preview_controller.dart",
  "language": "dart",
  "layer": "presentation/controller",
  "purpose": "Controls preview screen state and starts image generation flow.",
  "imports": [
    "package:get/get.dart"
  ],
  "classes": [
    "PreviewController"
  ],
  "main_symbols": [
    "PreviewController.startGeneration",
    "PreviewController.pickImage",
    "PreviewController.selectedImage",
    "PreviewController.isGenerating"
  ],
  "related_features": [
    "preview",
    "image_generation"
  ],
  "related_files": [
    "lib/presentation/view/screen/preview/preview_screen.dart",
    "lib/data/remote/repositories/api_repository.dart"
  ],
  "keywords": [
    "preview",
    "generation",
    "face swap",
    "controller"
  ],
  "risks": [
    "Generation flow depends on selected image and selected face state."
  ]
}
```

---

# REQUIRED SYMBOL OUTPUT

Whenever generating or updating Flutter indexes:

ALWAYS maintain:

- `.ai/indexes/symbols/flutter_symbols.json`

Symbol indexes are mandatory.

Indexes and symbol files are part of the source of truth.

Never leave them outdated after code modifications.

---

# REQUIRED FLUTTER SYMBOL INDEXING

For every important Dart entity, generate/update symbols:

- widgets
- screens
- controllers
- bindings
- services
- repositories
- managers
- models
- methods/functions
- constructors
- routes
- Rx variables
- API methods
- MethodChannel calls
- callbacks
- constants
- enums

---

# REQUIRED FLUTTER SYMBOL STRUCTURE

`.ai/indexes/symbols/flutter_symbols.json` must follow this structure:

```json
{
  "project_name": "",
  "platform": "flutter",
  "language": "dart",
  "symbols": [
    {
      "name": "",
      "qualified_name": "",
      "type": "",
      "file": "",
      "owner": "",
      "signature": "",
      "start_line": 0,
      "end_line": 0,
      "visibility": "",
      "is_async": false,
      "parameters": [],
      "return_type": "",
      "calls": [],
      "called_by": [],
      "reads_state": [],
      "writes_state": [],
      "navigation_actions": [],
      "api_calls": [],
      "storage_actions": [],
      "method_channel_calls": [],
      "side_effects": [],
      "related_symbols": [],
      "related_files": [],
      "tags": [],
      "risks": []
    }
  ]
}
```

---

# EXAMPLE SYMBOL ENTRY

```json
{
  "name": "startGeneration",
  "qualified_name": "PreviewController.startGeneration",
  "type": "method",
  "platform": "flutter",
  "language": "dart",
  "file": "lib/presentation/view/screen/preview/preview_controller.dart",
  "owner": "PreviewController",
  "signature": "Future<void> startGeneration()",
  "start_line": 70,
  "end_line": 112,
  "visibility": "public",
  "is_async": true,
  "parameters": [],
  "return_type": "Future<void>",
  "calls": [
    "ApiRepository.generateImage",
    "Get.toNamed"
  ],
  "called_by": [
    "PreviewScreen.generateButton.onTap"
  ],
  "reads_state": [
    "PreviewController.selectedImage",
    "PreviewController.selectedFace"
  ],
  "writes_state": [
    "PreviewController.isGenerating"
  ],
  "navigation_actions": [
    "Routes.result"
  ],
  "api_calls": [
    "POST /generate"
  ],
  "storage_actions": [],
  "method_channel_calls": [],
  "side_effects": [
    "Shows loading state",
    "Navigates to result screen"
  ],
  "related_symbols": [
    "PreviewScreen.buildContent",
    "ApiRepository.generateImage"
  ],
  "related_files": [
    "lib/presentation/view/screen/preview/preview_screen.dart",
    "lib/data/remote/repositories/api_repository.dart"
  ],
  "tags": [
    "preview",
    "generation",
    "face_swap",
    "navigation"
  ],
  "risks": []
}
```

---

# AUTOMATIC FLUTTER SYMBOL MAINTENANCE

Whenever:

- creating code
- editing code
- refactoring
- renaming functions/classes/routes
- adding APIs
- changing navigation
- adding MethodChannel calls
- changing state variables
- changing controller lifecycle logic

ALWAYS update:

- `.ai/indexes/symbols/flutter_symbols.json`
- caller/callee relationships
- related flows
- related feature indexes
- `.ai/indexes/codeindex_flutter.json` references if affected

Never leave symbol indexes outdated.

Do NOT regenerate full symbol indexes unless necessary.

Prefer incremental updates for changed symbols only.

---

# SYMBOL QUERY RULES

Before opening full source files:

1. Search `.ai/indexes/symbols/flutter_symbols.json` first.

2. Search by:
   - exact symbol name
   - qualified name
   - class name
   - owner
   - tags
   - callers/callees
   - routes
   - API methods
   - MethodChannel names
   - feature keywords

3. Only open source files if:
   - implementation details are required
   - the symbol index lacks information
   - architecture tracing fails
   - code editing is required
   - the symbol index seems outdated

Prefer symbol-level retrieval over full file scanning.

---

# CROSS-LANGUAGE BRIDGE TRACKING

Track Flutter ↔ Android native bridges:

```text
Flutter widget/controller
→ MethodChannel.invokeMethod(...)
→ Android MethodChannel handler
→ Native manager/service
→ callback/result
→ Flutter state update
```

Maintain symbol links between:

- Flutter methods
- MethodChannel calls
- Kotlin handlers
- Native callbacks
- Ads callbacks
- Billing callbacks

Cross-language bridge details should be stored in both:

- `.ai/indexes/symbols/flutter_symbols.json`
- `.ai/indexes/symbols/android_symbols.json`

when both sides exist.

---

# QUERY RULES

Before answering Flutter/Dart questions:

1. Read `.ai/indexes/codeindex_flutter.json` for architecture, feature, and flow context.
2. Read `.ai/indexes/symbols/flutter_symbols.json` for exact function/class/route lookup.
3. Search by:
   - feature name
   - flow name
   - class name
   - function name
   - route name
   - symbol name
   - keyword
4. Use line ranges from `.ai/indexes/symbols/flutter_symbols.json`.
5. Only open full source files if:
   - the function body is needed
   - the index is missing details
   - code editing is required
   - the index seems outdated

Avoid reading entire files when symbol-level index already answers the question.

---

# RESPONSE STYLE

Be concise, technical, and traceable.

Always mention:
- file path
- symbol name
- function/method name when relevant
- related flow when relevant

Prefer:
- flow chains
- function relationships
- symbol references
- file relationships

Avoid:
- generic summaries
- duplicating data from source files
- reading full files when symbols are enough

---

# OPTIMIZATION PRIORITIES

Always prioritize:

- architecture-level code index
- symbol-level retrieval
- function-level tracing through symbols
- caller/callee relationships
- low token usage
- incremental symbol updates
- cross-language tracing
- semantic searchability
