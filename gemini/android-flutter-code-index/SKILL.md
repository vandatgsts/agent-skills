---
name: flutter-function-level-indexing
description: Creates deep semantic indexes for Flutter/Dart projects at function level. Use when working with large Flutter codebases, tracing feature flows, debugging controllers/routes/API calls, reducing token usage, or understanding architecture without rereading entire files.
---

# FLUTTER / DART CODE INDEXING SKILL

You are a Flutter/Dart Codebase Indexing Agent.

Your responsibility is to analyze and maintain a function-level semantic index for the Flutter/Dart side of this project.

The goal is to make Flutter code easy to query without rereading entire source files.

---

# OUTPUT FILES

Always maintain these files at project root:

- CODE_INDEX_FLUTTER.md
- codeindex_flutter.json

Do not generate shallow indexes.
Do not only list file paths.
Every important Dart file must be indexed at class/function level.

---

# SCAN SCOPE

Analyze:

- lib/**/*.dart
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

- build/
- .dart_tool/
- generated files
- *.g.dart
- *.freezed.dart
- *.gr.dart
- .idea/
- .vscode/
- android/build/
- ios/Pods/

---

# REQUIRED FILE INDEX

For every important Dart file, collect:

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
- top-level functions
- state variables
- functions
- function signatures
- start_line
- end_line
- called_functions
- callers
- reads_state
- writes_state
- api_calls
- navigation_actions
- storage_actions
- method_channel_calls
- side_effects
- related_files
- keywords
- risks
- TODO/FIXME notes

---

# FUNCTION-LEVEL INDEX REQUIREMENT

For every function/method, always include:

```json
{
  "name": "",
  "signature": "",
  "start_line": 0,
  "end_line": 0,
  "visibility": "public/private",
  "is_async": false,
  "parameters": [],
  "return_type": "",
  "purpose": "",
  "called_functions": [],
  "callers": [],
  "reads_state": [],
  "writes_state": [],
  "api_calls": [],
  "navigation_actions": [],
  "storage_actions": [],
  "method_channel_calls": [],
  "side_effects": [],
  "related_files": [],
  "keywords": [],
  "risks": []
}
```

The index must be detailed enough to answer most architecture/debug questions without opening the full source file.

---

# FLUTTER-SPECIFIC DETECTION

Detect and index:

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

Represent flow steps like:

```json
{
  "name": "Image Generation Flow",
  "steps": [
    {
      "file": "lib/presentation/view/screen/preview/preview_controller.dart",
      "class": "PreviewController",
      "function": "startGeneration",
      "line": 80,
      "action": "Starts image generation and navigates to result screen"
    }
  ]
}
```

---

# REQUIRED JSON STRUCTURE

`codeindex_flutter.json` must follow this structure:

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
  "files": [
    {
      "path": "",
      "language": "dart",
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
  "path": "lib/presentation/view/screen/preview/preview_controller.dart",
  "language": "dart",
  "layer": "presentation/controller",
  "purpose": "Controls preview screen state and starts image generation flow.",
  "imports": [
    "package:get/get.dart"
  ],
  "classes": [
    {
      "name": "PreviewController",
      "type": "class",
      "extends": "AppBaseController",
      "mixins": [],
      "implements": [],
      "start_line": 10,
      "end_line": 160,
      "state_variables": [
        {
          "name": "isGenerating",
          "type": "RxBool",
          "line": 18,
          "purpose": "Tracks generation loading state"
        }
      ],
      "functions": [
        {
          "name": "startGeneration",
          "signature": "Future<void> startGeneration()",
          "start_line": 70,
          "end_line": 112,
          "visibility": "public",
          "is_async": true,
          "parameters": [],
          "return_type": "Future<void>",
          "purpose": "Starts face swap generation then navigates to result screen.",
          "called_functions": [
            "apiRepository.generateImage",
            "Get.toNamed"
          ],
          "callers": [
            "PreviewScreen.generateButton.onTap"
          ],
          "reads_state": [
            "selectedImage",
            "selectedFace"
          ],
          "writes_state": [
            "isGenerating"
          ],
          "api_calls": [
            "POST /generate"
          ],
          "navigation_actions": [
            "Routes.result"
          ],
          "method_channel_calls": [],
          "side_effects": [
            "Shows loading state",
            "Navigates to result screen"
          ],
          "related_files": [
            "lib/presentation/view/screen/preview/preview_screen.dart",
            "lib/data/remote/repositories/api_repository.dart"
          ],
          "keywords": [
            "preview",
            "generation",
            "face swap",
            "result"
          ],
          "risks": []
        }
      ]
    }
  ],
  "related_files": [],
  "keywords": ["preview", "generation", "controller"],
  "risks": []
}
```

---

# QUERY RULES

Before answering Flutter/Dart questions:

1. Read `codeindex_flutter.json` first.
2. Search by function name, class name, route name, keyword, or flow name.
3. Use line ranges from the index.
4. Only open full source files if:
   - the function body is needed
   - the index is missing details
   - code editing is required
   - the index seems outdated

Avoid reading entire files when function-level index already answers the question.

---

# RESPONSE STYLE

Be concise, technical, and traceable.
Always mention file path and function name when relevant.
Prefer flow chains and function relationships over generic summaries.
