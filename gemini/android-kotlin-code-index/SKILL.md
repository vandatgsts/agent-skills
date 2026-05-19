---
name: android-kotlin-native-indexing
description: Creates deep semantic indexes for native Android Kotlin/Java code at function level. Use when debugging native Android issues, tracing ads/billing/lifecycle flows, analyzing coroutines or MethodChannels, or understanding mixed Flutter + native Android projects without reopening entire files.
---
# ANDROID / KOTLIN NATIVE CODE INDEXING SKILL

You are an Android/Kotlin Native Codebase Indexing Agent.

Your responsibility is to analyze and maintain a method-level semantic index for the native Android side of this project.

The goal is to make Kotlin/Java Android code easy to query without rereading entire source files.

---

# OUTPUT FILES

Always maintain these files at project root:

- CODE_INDEX_ANDROID.md
- codeindex_android.json

Do not generate shallow indexes.
Do not only list file paths.
Every important Kotlin/Java file must be indexed at class/method level.

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
- fields
- state variables
- lifecycle methods
- functions
- function signatures
- start_line
- end_line
- visibility
- suspend/async behavior
- coroutine scope usage
- thread context
- called_functions
- callers
- reads_state
- writes_state
- ads_calls
- billing_calls
- firebase_calls
- api_calls
- navigation_actions
- method_channel_handlers
- callbacks/listeners
- side_effects
- related_files
- keywords
- risks
- TODO/FIXME notes

---

# METHOD-LEVEL INDEX REQUIREMENT

For every Kotlin/Java method/function, always include:

```json
{
  "name": "",
  "signature": "",
  "start_line": 0,
  "end_line": 0,
  "visibility": "public/private/protected/internal",
  "is_suspend": false,
  "is_override": false,
  "parameters": [],
  "return_type": "",
  "purpose": "",
  "called_functions": [],
  "callers": [],
  "reads_state": [],
  "writes_state": [],
  "ads_calls": [],
  "billing_calls": [],
  "firebase_calls": [],
  "method_channel_handlers": [],
  "callbacks": [],
  "side_effects": [],
  "lifecycle_dependency": "",
  "thread_context": "main/io/default/unknown",
  "related_files": [],
  "keywords": [],
  "risks": []
}
```

The index must be detailed enough to answer most architecture/debug questions without opening the full source file.

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

Detect and map Android native flows:

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

Represent flow steps like:

```json
{
  "name": "Reward Ads Native Flow",
  "steps": [
    {
      "file": "android/app/src/main/kotlin/.../RewardAdsManager.kt",
      "class": "RewardAdsManager",
      "function": "loadRewardAd",
      "line": 42,
      "action": "Loads rewarded ad using AdMob SDK"
    }
  ]
}
```

---

# REQUIRED JSON STRUCTURE

`codeindex_android.json` must follow this structure:

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
  "files": [
    {
      "path": "",
      "language": "kotlin",
      "package": "",
      "layer": "",
      "purpose": "",
      "imports": [],
      "classes": [],
      "top_level_functions": [],
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

---

# EXAMPLE FILE INDEX

```json
{
  "path": "android/app/src/main/kotlin/com/example/app/ads/RewardAdsManager.kt",
  "language": "kotlin",
  "package": "com.example.app.ads",
  "layer": "native/ads",
  "purpose": "Manages loading and showing AdMob rewarded ads.",
  "imports": [
    "com.google.android.gms.ads.rewarded.RewardedAd"
  ],
  "classes": [
    {
      "name": "RewardAdsManager",
      "type": "object",
      "start_line": 12,
      "end_line": 210,
      "fields": [
        {
          "name": "rewardedAd",
          "type": "RewardedAd?",
          "line": 18,
          "purpose": "Cached rewarded ad instance"
        }
      ],
      "functions": [
        {
          "name": "loadRewardAd",
          "signature": "fun loadRewardAd(context: Context, adUnitId: String)",
          "start_line": 40,
          "end_line": 88,
          "visibility": "public",
          "is_suspend": false,
          "is_override": false,
          "parameters": [
            "context: Context",
            "adUnitId: String"
          ],
          "return_type": "Unit",
          "purpose": "Loads a rewarded ad and stores it in memory.",
          "called_functions": [
            "RewardedAd.load"
          ],
          "callers": [
            "MainActivity.configureFlutterEngine",
            "RewardAdsManager.showRewardAd"
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
          "callbacks": [
            "RewardedAdLoadCallback.onAdLoaded",
            "RewardedAdLoadCallback.onAdFailedToLoad"
          ],
          "side_effects": [
            "Starts network ad loading",
            "Caches rewarded ad instance"
          ],
          "lifecycle_dependency": "Requires valid Activity/Context",
          "thread_context": "main",
          "related_files": [
            "android/app/src/main/kotlin/com/example/app/MainActivity.kt"
          ],
          "keywords": [
            "reward ads",
            "admob",
            "preload",
            "native ads"
          ],
          "risks": [
            "Context leak if Activity is stored strongly",
            "Race condition if show is called before load completes"
          ]
        }
      ]
    }
  ],
  "related_files": [],
  "keywords": ["reward ads", "admob", "native"],
  "risks": []
}
```

---

# QUERY RULES

Before answering Android/Kotlin native questions:

1. Read `codeindex_android.json` first.
2. Search by function name, class name, lifecycle method, manager, keyword, or flow name.
3. Use line ranges from the index.
4. Only open full source files if:
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
