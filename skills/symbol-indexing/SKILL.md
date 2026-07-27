---
name: symbol-indexing
description: Builds and maintains global symbol lookup indexes for Flutter/Dart and Android Kotlin/Java projects. Use when you need fast lookup of classes, methods, functions, routes, state variables, API calls, MethodChannels, callbacks, or caller/callee relationships without reopening full source files.
---

# SYMBOL INDEXING SKILL

You are a Symbol Indexing Agent.

Your responsibility is to build and maintain fast lookup indexes for all important named code entities in the project.

The goal is:
- find functions/classes quickly
- reduce token usage
- avoid reopening full source files
- support caller/callee tracing
- support feature flow tracing
- connect Flutter and native Android symbols

---

# Persistent Symbol Files

Always maintain:

## Flutter
- `.ai/indexes/symbols/flutter_symbols.json`

## Android Native
- `.ai/indexes/symbols/android_symbols.json`

For mixed Flutter + native Android projects, maintain both.

## Manifest And Shard Awareness

When a root symbol file has a v2 manifest schema, it is an entry point only. Keep detailed symbols in the shard files declared by that manifest; do not replace the manifest with a flat `symbols` array.

- Android: `.ai/indexes/symbols/android_symbols.json` + `.ai/indexes/symbols/android/*.json`
- Flutter: `.ai/indexes/symbols/flutter_symbols.json` + `.ai/indexes/symbols/flutter/*.json`

After a rename, move, package change, route change, or structural refactor, update affected symbols and caller/callee links. Then run the platform sharding script with `--rebalance` followed by `--validate`. Validation confirms shard integrity, so also compare symbol `file` paths against the source tree.

---

# What Counts As A Symbol

A symbol is any important named code entity.

## Flutter / Dart Symbols

Track:
- class
- widget
- controller
- binding
- service
- repository
- model
- enum
- extension
- mixin
- function
- method
- constructor
- field
- Rx variable
- route
- API method
- API endpoint
- MethodChannel name
- MethodChannel method call
- callback
- constant

## Android / Kotlin Symbols

Track:
- class
- object
- interface
- enum
- annotation
- activity
- fragment
- viewmodel
- service
- receiver
- worker
- repository
- manager
- function
- suspend function
- extension function
- property
- StateFlow
- SharedFlow
- LiveData
- lifecycle method
- listener
- callback
- ads callback
- billing callback
- Firebase method
- MethodChannel handler
- constant

---

# Required Symbol Schema

Every symbol must include:

```json
{
  "name": "",
  "qualified_name": "",
  "type": "",
  "language": "",
  "platform": "",
  "file": "",
  "owner": "",
  "signature": "",
  "start_line": 0,
  "end_line": 0,
  "visibility": "",
  "is_async": false,
  "is_suspend": false,
  "parameters": [],
  "return_type": "",
  "calls": [],
  "called_by": [],
  "reads_state": [],
  "writes_state": [],
  "side_effects": [],
  "related_symbols": [],
  "related_files": [],
  "tags": [],
  "notes": ""
}
