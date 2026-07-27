---
name: android-kotlin-native-indexing
description: Creates architecture-level Android code indexes and maintains Android symbol indexes for method-level lookup.
---
# ANDROID / KOTLIN NATIVE CODE INDEXING SKILL

You are an Android/Kotlin Native Codebase Indexing Agent.

Your responsibility is to analyze and maintain an architecture-level Android code index for the native Android side of this project, while storing detailed method-level metadata in:

- `.ai/indexes/symbols/android_symbols.json`

The goal is to make Kotlin/Java Android code easy to query without rereading entire source files.

---

# OUTPUT FILES

Maintain these entry files:

- `.ai/indexes/CODE_INDEX_ANDROID.md`
- `.ai/indexes/codeindex_android.json`

When `.ai/indexes/codeindex_android.json` uses `schema: "android-index-manifest-v2"`, treat it as a manifest, not a complete monolithic index. Maintain the shard pairs it declares:

- `.ai/indexes/android/<shard>.json` for architecture/file data
- `.ai/indexes/symbols/android/<shard>.json` for detailed symbols
- `.ai/indexes/symbols/android_symbols.json` as the symbol manifest

Never flatten or replace a v2 manifest with a legacy single-file index. After Kotlin/Java additions, moves, renames, or package refactors, update the affected shard content, then run:

```powershell
python <skill-dir>/scripts/shard_android_indexes.py <project-root> --rebalance
python <skill-dir>/scripts/shard_android_indexes.py <project-root> --validate
```

`--validate` checks manifest/shard integrity; it does not prove that paths match source. Compare indexed paths with the source tree after structural refactors.

Do not generate shallow indexes.
Do not only list file paths.
Every important Kotlin/Java file must be indexed at architecture and feature level.

Detailed method-level indexing must be stored in:

- `.ai/indexes/symbols/android_symbols.json`

---

# SCAN SCOPE

Analyze:

- android/app/src/**/*.kt
- android/app/src/**/*.java
- app/src/**/*.kt
- app/src/**/*.java
- native Android modules
- Activities
- Fragments
- ViewModels
- Services
- BroadcastReceivers
- Workers
- Managers
- Repositories
- Ad managers
- Billing managers
- Firebase services
- MethodChannel handlers
- platform-specific image processing
- native SDK integrations

Ignore:

- build/
- .gradle/
- .idea/
- generated/
- android/build/
- app/build/
- R.java
- BuildConfig.java
- generated view binding files

---

# REQUIRED FILE INDEX

For every important Kotlin/Java file, collect:

- path
- language
- package
- layer
- purpose
- imports
- classes
- objects
- interfaces
- companion objects
- important properties
- related_files
- keywords
- risks
- TODO/FIXME notes

---
# ANDROID/KOTLIN-SPECIFIC DETECTION

Detect and index:

- Application class
- MainActivity
- Activity lifecycle
- Fragment lifecycle
- ViewModel
- AndroidViewModel
- Hilt/Dagger injection
- Koin injection
- singleton objects
- companion objects
- init blocks
- coroutines
- lifecycleScope
- viewModelScope
- GlobalScope usage
- Flow
- StateFlow
- SharedFlow
- LiveData
- callbacks
- listeners
- BroadcastReceiver
- Service
- WorkManager
- Room
- Retrofit
- OkHttp interceptors
- Firebase
- Remote Config
- Analytics
- Crashlytics
- AdMob
- App Open Ads
- Interstitial Ads
- Rewarded Ads
- Native Ads
- BillingClient
- ProductDetails
- purchase callbacks
- premium checks
- MethodChannel.setMethodCallHandler
- MethodChannel.Result callbacks

---

# LIFECYCLE METHOD DETECTION

Specially index these methods when present:

- onCreate
- onStart
- onResume
- onPause
- onStop
- onDestroy
- onCreateView
- onViewCreated
- onDestroyView
- onActivityResult
- onRequestPermissionsResult
- onNewIntent
- configureFlutterEngine
- cleanUpFlutterEngine
- onMethodCall

For lifecycle methods, include:

- lifecycle_dependency
- registered callbacks
- removed callbacks
- possible leak risks
- thread risks
- UI side effects

---

# FLUTTER NATIVE BRIDGE DETECTION

When Kotlin code connects to Flutter, index:

- MethodChannel name
- method names handled
- arguments read
- result.success/result.error/result.notImplemented
- native class handling the call
- Flutter file likely invoking it
- async behavior
- thread context

Example:

```json
{
  "channel": "face_swap/native_ads",
  "method": "loadRewardAd",
  "handler_file": "android/app/src/main/kotlin/.../MainActivity.kt",
  "handler_function": "configureFlutterEngine",
  "native_target": "RewardAdsManager.loadAd",
  "called_by_flutter": [
    "lib/core/native/native_ads_channel.dart"
  ]
}
```

---

# ADS / BILLING SPECIAL INDEXING

For ads-related files, always detect:

- ad type
- ad unit source
- preload logic
- show logic
- callbacks
- failure handling
- retry logic
- premium gating
- lifecycle cleanup
- race condition risks

For billing-related files, always detect:

- product IDs
- BillingClient connection
- queryProductDetailsAsync
- launchBillingFlow
- purchasesUpdatedListener
- acknowledgePurchase
- restore purchase
- premium state update
- failure handling

---

# FLOW MAPPING

Detect and map Android native flows.

Also group flows into related features when possible.

Examples of flows to detect:

- app startup flow
- splash native flow
- app open ad flow
- interstitial ad flow
- reward ad flow
- native ad flow
- billing flow
- premium check flow
- Firebase Remote Config flow
- MethodChannel bridge flow
- native image processing flow
- permission flow

Each flow should:
- reference related features
- reference related symbols
- reference important files
- describe flow transitions
- describe important side effects
- describe native ↔ Flutter interactions when applicable

Represent flow steps like:

```json
{
  "name": "Reward Ads Native Flow",
  "feature": "reward_ads",
  "steps": [
    {
      "file": "android/app/src/main/kotlin/.../RewardAdsManager.kt",
      "symbol": "RewardAdsManager.loadRewardAd",
      "action": "Loads rewarded ad using AdMob SDK"
    },
    {
      "file": "android/app/src/main/kotlin/.../RewardAdsManager.kt",
      "symbol": "RewardAdsManager.showRewardAd",
      "action": "Displays rewarded ad and waits for reward callback"
    }
  ],
  "related_symbols": [
    "RewardAdsManager.loadRewardAd",
    "RewardAdsManager.showRewardAd",
    "MainActivity.configureFlutterEngine"
  ],
  "related_features": [
    "reward_ads",
    "premium"
  ]
}
```
---
# REQUIRED JSON STRUCTURE

`.ai/indexes/codeindex_android.json` must follow this structure:

```json
{
  "project_name": "",
  "platform": "android_native",
  "language": "kotlin/java",
  "architecture": "",
  "dependency_injection": "",
  "modules": [],
  "entry_points": [],
  "method_channels": [],
  "ads": [],
  "billing": [],
  "flows": [],
  "features": [],
  "files": [
    {
      "path": "",
      "language": "kotlin",
      "package": "",
      "layer": "",
      "purpose": "",
      "imports": [],
      "classes": [],
      "objects": [],
      "interfaces": [],
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

- `.ai/indexes/symbols/android_symbols.json`

Do not store detailed method/function metadata inside `.ai/indexes/codeindex_android.json`, including:
- full signatures
- line ranges
- caller/callee graphs
- state reads/writes
- side effects
- callback chains
- thread context

Those belong in:

- `.ai/indexes/symbols/android_symbols.json`
---

# EXAMPLE CODE INDEX FILE ENTRY

```json
{
  "path": "android/app/src/main/kotlin/com/example/app/ads/RewardAdsManager.kt",
  "language": "kotlin",
  "package": "com.example.app.ads",
  "layer": "native/ads",
  "purpose": "Handles rewarded ad loading and display flow.",
  "imports": [
    "com.google.android.gms.ads.rewarded.RewardedAd"
  ],
  "classes": [
    "RewardAdsManager"
  ],
  "objects": [],
  "interfaces": [],
  "main_symbols": [
    "RewardAdsManager.loadRewardAd",
    "RewardAdsManager.showRewardAd",
    "RewardAdsManager.rewardedAd"
  ],
  "related_features": [
    "reward_ads",
    "premium"
  ],
  "related_files": [
    "android/app/src/main/kotlin/com/example/app/MainActivity.kt"
  ],
  "keywords": [
    "reward ads",
    "admob",
    "premium"
  ],
  "risks": [
    "Reward flow depends on valid Activity lifecycle."
  ]
}
```
---
# QUERY RULES

Before answering Android/Kotlin native questions:

1. Read `.ai/indexes/codeindex_android.json` for architecture, feature, and flow context.
2. Read `.ai/indexes/symbols/android_symbols.json` for exact method/class lookup.
3. Search symbol index by function name, class name, lifecycle method, manager, callback, MethodChannel handler, keyword, or flow name.
4. Use line ranges from `android_symbols.json`.
5. Only open full source files if:
   - the method body is needed
   - the index is missing details
   - code editing is required
   - the index seems outdated

Avoid reading entire files when method-level index already answers the question.

---

# RESPONSE STYLE

Be concise, technical, and traceable.
Always mention file path and method name when relevant.
Prefer lifecycle chains, callback chains, and dependency relationships over generic summaries.

# REQUIRED SYMBOL OUTPUT

Whenever generating or updating Android native indexes:

ALWAYS maintain:

- `.ai/indexes/symbols/android_symbols.json`

Do not only generate:
- `.ai/indexes/CODE_INDEX_ANDROID.md`
- `.ai/indexes/codeindex_android.json`

Symbol indexes are mandatory.

Indexes and symbol files are part of the source of truth.

Never leave them outdated after code modifications.

---

# REQUIRED ANDROID SYMBOL INDEXING

For every important Kotlin/Java entity, generate/update symbols:

- Activities
- Fragments
- ViewModels
- Managers
- Services
- Repositories
- methods/functions
- suspend functions
- lifecycle methods
- StateFlow/SharedFlow
- ads callbacks
- billing callbacks
- Firebase handlers
- MethodChannel handlers
- listeners
- constants

---
# REQUIRED ANDROID SYMBOL STRUCTURE

`.ai/indexes/symbols/android_symbols.json` must follow this structure:

```json
{
  "project_name": "",
  "platform": "android_native",
  "language": "kotlin/java",
  "symbols": []
}
```
---
# REQUIRED ANDROID SYMBOL METADATA

Every Android symbol must include:

```json
{
  "name": "",
  "qualified_name": "",
  "type": "",
  "platform": "android",
  "language": "kotlin",
  "file": "",
  "owner": "",
  "signature": "",
  "start_line": 0,
  "end_line": 0,
  "is_suspend": false,
  "calls": [],
  "called_by": [],
  "reads_state": [],
  "writes_state": [],
  "ads_calls": [],
  "billing_calls": [],
  "firebase_calls": [],
  "method_channel_handlers": [],
  "callbacks": [],
  "side_effects": [],
  "lifecycle": "",
  "related_symbols": [],
  "related_files": [],
  "thread_context": "",
  "risks": [],
  "tags": []
}
```
---
# EXAMPLE SYMBOL ENTRY

```json
{
  "name": "loadRewardAd",
  "qualified_name": "RewardAdsManager.loadRewardAd",
  "type": "method",
  "platform": "android",
  "language": "kotlin",
  "file": "android/app/src/main/kotlin/com/example/app/ads/RewardAdsManager.kt",
  "owner": "RewardAdsManager",
  "signature": "fun loadRewardAd(context: Context, adUnitId: String)",
  "start_line": 40,
  "end_line": 88,
  "is_suspend": false,
  "calls": [
    "RewardedAd.load"
  ],
  "called_by": [
    "MainActivity.configureFlutterEngine"
  ],
  "reads_state": [],
  "writes_state": [
    "rewardedAd",
    "isLoading"
  ],
  "ads_calls": [
    "RewardedAd.load"
  ],
  "billing_calls": [],
  "firebase_calls": [],
  "method_channel_handlers": [
    "loadRewardAd"
  ],
  "side_effects": [
    "Caches rewarded ad instance"
  ],
  "related_symbols": [
    "RewardAdsManager.showRewardAd"
  ],
  "related_files": [
    "android/app/src/main/kotlin/com/example/app/MainActivity.kt"
  ],
  "thread_context": "main",
  "tags": [
    "reward_ads",
    "admob"
  ]
}
```
---

# AUTOMATIC ANDROID SYMBOL MAINTENANCE

Whenever:
- creating code
- editing code
- refactoring
- renaming functions/classes/routes
- changing lifecycle logic
- changing ads/billing logic
- changing MethodChannel handlers

ALWAYS update:
- `android_symbols.json`
- caller/callee relationships
- related flows
- related feature indexes

Never leave symbol indexes outdated.

Do NOT regenerate full symbol indexes unless necessary.

Prefer incremental updates for changed symbols only.

Update affected callers/callees transitively when symbol relationships change.

---

# SYMBOL QUERY RULES

Before opening full source files:

1. Search `android_symbols.json` first.

2. Search by:
   - exact symbol name
   - qualified name
   - tags
   - callers/callees
   - lifecycle methods
   - ads callbacks
   - billing callbacks
   - MethodChannel handlers
   - feature keywords

3. Only open source files if:
   - implementation details are required
   - the symbol index lacks information
   - architecture tracing fails
   - code editing is required

Prefer symbol-level retrieval over full file scanning.

---

# CROSS-LANGUAGE BRIDGE TRACKING

Track Flutter ↔ Android native bridges:

Flutter widget/controller
→ MethodChannel.invokeMethod(...)
→ Android MethodChannel handler
→ Native manager/service
→ callback/result
→ Flutter state update

Maintain symbol links between:
- Flutter MethodChannel calls
- Kotlin handlers
- Native managers
- Ads callbacks
- Billing callbacks

Track bidirectional relationships between:
- Flutter invokeMethod calls
- Android MethodChannel handlers
- returned callbacks/results
- Flutter state updates triggered by native results

---
# INDEX LAYER RESPONSIBILITY

Use:

- `.ai/indexes/codeindex_android.json`
for:
- architecture
- feature relationships
- module structure
- flow mapping
- important files

Use:

- `.ai/indexes/symbols/android_symbols.json`
for:
- exact method lookup
- caller/callee tracing
- line ranges
- state reads/writes
- callback chains
- side effects
- ads/billing tracing
- lifecycle tracing

Never duplicate deep method-level metadata inside `.ai/indexes/codeindex_android.json`.

Avoid storing duplicated semantic data across:
- code indexes
- symbol indexes
- feature indexes

Each retrieval layer should have a distinct responsibility.

---
# LARGE PROJECT OPTIMIZATION

For large Android projects:

- prefer incremental indexing
- avoid regenerating full indexes
- update only affected modules/files/symbols
- preserve stable symbol references
- preserve existing flow mappings when unchanged

---
# OPTIMIZATION PRIORITIES

Always prioritize:
- symbol-level retrieval
- function-level tracing
- caller/callee relationships
- low token usage
- incremental symbol updates
- cross-language tracing
- semantic searchability
