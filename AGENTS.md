# Global Workflow Rules

- Always respond in Vietnamese.
- Indexes, symbol files, and bug memory files are part of the source of truth.
- Never leave them outdated after any code modification or generation.

---

# Workspace Initialization Rules

Whenever initializing a new workspace or starting a new session in a project:

1. Detect the project type:
   - Flutter/Dart
   - Native Android Kotlin/Java
   - Mixed Flutter + Native Android

2. Activate the appropriate indexing skills:
   - `flutter-code-indexing`
   - `android-kotlin-native-indexing`
   - `symbol-indexing`
   - `runtime-ui-inspection` when a running app surface is available for UI validation
   - `android-compose-ui` when changing Jetpack Compose presentation
   - `android-testing` when validating behavior or a bug fix
   - `flutter-testing` when validating Flutter behavior or a Flutter bug fix
   - `mobile-ads-orchestration` when changing or debugging ads, rewards, premium ad removal, or ad loading UI

3. Generate or verify all required indexes and symbol maps simultaneously.

---

# Pre-Generation & Planning Rules

Before generating any new code, components, or modules:

1. **Architecture Planning**: ALWAYS draft a brief execution plan outlining the proposed architecture, file paths, targeted symbols, and state management flow.
2. **User Clarification**: DO NOT write or generate code immediately if there are ambiguities. Ask the user concise questions regarding:
   - Business logic requirements
   - Edge cases or error handling expectations
   - Context requirements (e.g., Coroutine/Thread contexts, Rx/StateFlow bindings)
   - Dependency preferences
3. Wait for the user's confirmation or feedback before starting the generation pipeline.

---

# Required Flutter Index Files

Maintain:
- `.ai/indexes/CODE_INDEX_FLUTTER.md`
- `.ai/indexes/codeindex_flutter.json` (entry index or v2 manifest)
- `.ai/indexes/symbols/flutter_symbols.json` (entry symbol index or v2 manifest)

When Flutter index files use a v2 manifest schema, also maintain the declared shards in:
- `.ai/indexes/flutter/*.json`
- `.ai/indexes/symbols/flutter/*.json`

---

# Required Android Native Index Files

Maintain:
- `.ai/indexes/CODE_INDEX_ANDROID.md`
- `.ai/indexes/codeindex_android.json` (entry index or v2 manifest)
- `.ai/indexes/symbols/android_symbols.json` (entry symbol index or v2 manifest)

When Android index files use a v2 manifest schema, also maintain the declared shards in:
- `.ai/indexes/android/*.json`
- `.ai/indexes/symbols/android/*.json`

---

# Mixed Flutter + Native Android Projects

For mixed projects:
- maintain Flutter and Android indexes separately
- maintain cross-platform symbol links
- track MethodChannel bridges between Flutter and native Android

---

# Continuous Indexing & Generation Rules

For every:
- code generation (newly generated files, boilerplate, or feature stubs)
- code modification
- architecture update
- refactor
- feature implementation
- dependency change
- function rename
- route change
- API change
- MethodChannel change

ALWAYS update simultaneously:
- code indexes (`.ai/indexes/CODE_INDEX_*.md` and `.ai/indexes/codeindex_*.json`)
- symbol indexes (`*_symbols.json`)
- related feature indexes
- bug memory (if applicable)

For v2 manifests, update affected shard content and preserve root manifests. After additions, moves, renames, or package refactors, run the platform sharding script with `--rebalance`, then `--validate`. Validation checks shard integrity only; compare indexed paths with the source tree after structural changes.

Never leave indexes or symbols outdated after completing a task or generating new code.
Prefer incremental updates over full regeneration.
Update only affected files/symbols when possible.

---

# Flutter Indexing Rules

When working with Flutter/Dart code:

Use:
- `flutter-code-indexing`

Maintain:
- `.ai/indexes/CODE_INDEX_FLUTTER.md`
- `.ai/indexes/codeindex_flutter.json`

Index at function-level including:
- widgets
- screens
- controllers
- bindings
- services
- repositories
- models
- routes
- API calls
- state variables
- Rx variables
- navigation flows
- MethodChannel calls
- async flows
- line ranges
- callers/callees
- side effects
- keywords
- tags

Avoid shallow file-only indexes.

---

# Android Native Indexing Rules

When working with native Android code:

Use:
- `android-kotlin-native-indexing`

Maintain:
- `.ai/indexes/CODE_INDEX_ANDROID.md`
- `.ai/indexes/codeindex_android.json`

Index at function-level including:
- Activities
- Fragments
- ViewModels
- Managers
- Services
- Repositories
- Coroutines
- Flow/StateFlow
- SharedFlow
- Ads/Billing callbacks
- Firebase integrations
- lifecycle methods
- MethodChannel handlers
- line ranges
- callers/callees
- side effects
- thread/coroutine context
- keywords
- tags

Avoid shallow file-only indexes.

---

# Symbol Indexing Rules

Always use:
- `symbol-indexing`
together with platform indexing skills.

---

# Required Symbol Files

Maintain:

Flutter:
- `.ai/indexes/symbols/flutter_symbols.json`
- declared `.ai/indexes/symbols/flutter/*.json` shards when using v2 manifests

Android Native:
- `.ai/indexes/symbols/android_symbols.json`
- declared `.ai/indexes/symbols/android/*.json` shards when using v2 manifests

---

# What Must Be Indexed As Symbols

## Flutter/Dart

Track:
- classes
- widgets
- controllers
- bindings
- repositories
- services
- methods/functions
- constructors
- Rx variables
- routes
- API methods
- MethodChannel calls
- callbacks
- constants
- enums

---

## Android/Kotlin

Track:
- classes
- objects
- interfaces
- Activities
- Fragments
- ViewModels
- Managers
- Services
- suspend functions
- StateFlow/SharedFlow
- lifecycle methods
- ads callbacks
- billing callbacks
- Firebase handlers
- MethodChannel handlers
- listeners
- constants

---

# Required Symbol Metadata

Every symbol must include:
- symbol name
- qualified name
- type
- platform
- language
- file path
- owner class/object
- signature
- start/end line
- callers
- callees
- state reads/writes
- side effects
- related symbols
- related files
- searchable tags

---

# Automatic Symbol Maintenance Rules

Whenever generating (creating new code), modifying, refactoring, renaming, or deleting code:

ALWAYS update symbol indexes incrementally at the exact same time as code indexes.

Update:
- newly generated or changed symbols
- affected callers/callees
- related flows
- related feature indexes

Do NOT leave stale symbol references.
Do NOT regenerate full symbol indexes unless necessary.

---

# Cross-Language Tracing Rules

For Flutter + native Android projects:

Track:
Flutter widget/controller
→ MethodChannel.invokeMethod(...)
→ Android MethodChannel handler
→ Native manager/service
→ callback/result
→ Flutter state update

Maintain symbol links between:
- Flutter methods
- MethodChannel calls
- Kotlin handlers
- Native callbacks

---

# Runtime UI Inspection Rules

When a user reports a visual, layout, state-rendering, navigation, tap-target, loading, empty, error, or accessibility issue in a running app:

1. Activate `runtime-ui-inspection`.
2. Capture a fresh screenshot before changing source code.
3. Save temporary evidence under `.ai/ui-inspections/<timestamp>/`.
4. Inspect the rendered UI, then trace the affected route, state, and UI symbol through indexes.
5. Re-capture the same scenario after a fix; do not treat a successful build as visual verification.

Never capture or retain unrelated windows, secrets, personal data, or notifications.

---

# Mobile Ads Rules

When a non-native ad is loading for display, show a single app-level loading overlay over the app and block duplicate interaction. Dismiss it only when the ad is handed to the SDK for display, attached to its banner placement, fails, times out, or is cancelled.

Native ads must not use the global loading overlay. Keep their layout stable with a local placeholder or skeleton at the native placement.

---

# Bug Resolution Workflow

## Pre-Fix Check

Before fixing any bug:

1. ALWAYS activate:
   - `bug-memory-tracking`
   - `debugging-and-error-recovery`
   - `runtime-ui-inspection` when the report concerns rendered UI or interaction behavior

2. Read:
   - `.ai/bugs/BUG_INDEX.md`
   - `.ai/bugs/bugindex.json` manifest
   - only matching `.ai/bugs/<feature>/BUG-<id>.json` shards

3. Search for:
   - similar symptoms
   - related crashes
   - regressions
   - previous failed fixes
   - related affected files/functions
   - related symbols

4. Reuse:
   - known root causes
   - verified fixes
   - stable implementations

Avoid repeating failed debugging attempts.

---

# Record & Update Rules

If the bug is new:

1. Create a new record in:
   - `.ai/bugs/<feature>/BUG-<id>.json` for complete details
   - `.ai/bugs/BUG_INDEX.md` and `.ai/bugs/bugindex.json` for the lightweight index entry

2. Set status:
   - `OPEN`
   or
   - `INVESTIGATING`

3. Record:
   - symptoms
   - logs/errors
   - reproduction steps
   - affected files
   - affected functions
   - affected symbols
   - suspected root cause

---

# After Fix Rules

After fixing a bug:

1. Update:
   - root cause
   - fix solution
   - fixed files
   - fixed functions
   - updated symbols
   - verification steps
   - regression notes

2. Change status:
   - `FIXED`
   or
   - `VERIFIED`

3. If applicable:
   - link related bugs
   - mark regressions
   - document risky areas

---

# Query & Debugging Rules

Before answering any code-related or debugging question:
Read all relevant indexes and symbol maps first.

---

# Flutter Retrieval Sources

Read:
- `.ai/indexes/CODE_INDEX_FLUTTER.md`
- `.ai/indexes/codeindex_flutter.json`
- `.ai/indexes/symbols/flutter_symbols.json`
- declared Flutter architecture and symbol shards when the root files are v2 manifests

---

# Android Retrieval Sources

Read:
- `.ai/indexes/CODE_INDEX_ANDROID.md`
- `.ai/indexes/codeindex_android.json`
- `.ai/indexes/symbols/android_symbols.json`
- declared Android architecture and symbol shards when the root files are v2 manifests

---

# Bug Retrieval Sources

Read:
- `.ai/bugs/BUG_INDEX.md`
- `.ai/bugs/bugindex.json`
- matching bug shard files declared by the manifest

---

# Retrieval Priority Rules

Search in this order:
1. symbol indexes
2. feature indexes
3. bug memory
4. code indexes
5. source files

---

# Symbol Lookup Rules

Before opening full source files:
Search symbol indexes first by:
- exact symbol name
- qualified name
- class name
- tags
- callers/callees
- feature keywords

---

# Source File Access Rules

Only open full source files if:
- the index lacks required details
- implementation inspection is necessary
- architecture tracing fails
- code modifications/generations are required

Otherwise rely on semantic indexes and symbol tables first.

---

# Review Rules

Before committing, merging, or releasing a non-trivial change, activate `code-review-and-quality`. Verify the relevant diff, build/test result, and runtime evidence before marking the work complete.

---

# Optimization Priorities

Always prioritize:
- function-level tracing
- semantic retrieval
- low token usage
- reuse of verified fixes
- avoiding repeated failed fixes
- architecture consistency
- incremental index & symbol maintenance
- caller/callee tracing
- symbol-level navigation
- cross-language tracing
