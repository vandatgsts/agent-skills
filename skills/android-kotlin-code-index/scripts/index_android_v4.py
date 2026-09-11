#!/usr/bin/env python3
"""Android adapter for the shared direct-write index engine."""
from __future__ import annotations

import sys
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[2]
COMMON_SCRIPTS = SKILLS_ROOT / "symbol-indexing" / "scripts"
if not COMMON_SCRIPTS.is_dir():
    raise SystemExit(f"Missing shared indexing scripts: {COMMON_SCRIPTS}")
sys.path.insert(0, str(COMMON_SCRIPTS))

from index_v4 import PlatformConfig, run  # noqa: E402


CONFIG = PlatformConfig(
    key="android",
    platform="android_native",
    language="kotlin/java",
    summary_markdown=".ai/indexes/CODE_INDEX_ANDROID.md",
    index_manifest=".ai/indexes/codeindex_android.json",
    symbol_manifest=".ai/indexes/symbols/android_symbols.json",
    architecture_dir=".ai/indexes/android",
    symbol_dir=".ai/indexes/symbols/android",
    source_globs=(
        "android/app/src/main/*.kt",
        "android/app/src/main/*.java",
        "android/app/src/main/**/*.kt",
        "android/app/src/main/**/*.java",
        "app/src/main/*.kt",
        "app/src/main/*.java",
        "app/src/main/**/*.kt",
        "app/src/main/**/*.java",
        "modules/*/src/main/*.kt",
        "modules/*/src/main/*.java",
        "modules/*/src/main/**/*.kt",
        "modules/*/src/main/**/*.java",
    ),
    excludes=(
        "**/build/**",
        "**/.gradle/**",
        "**/.idea/**",
        "**/generated/**",
        "**/R.java",
        "**/BuildConfig.java",
    ),
    concern_patterns=(
        ("duplicate-review", ("duplicate", "similarity", "perceptual", "dhash", "ahash")),
        ("enhancement", ("enhance", "brightness", "contrast", "gamma", "color balance", "black level")),
        ("detection", ("detect", "inference", "tflite", "tensorflow", "overlay", "corner")),
        ("capture", ("capture", "takepicture", "imageproxy", "camerax")),
        ("permission", ("permission", "required access", "activityresultcontracts")),
        ("billing", ("billing", "purchase", "subscription", "premium")),
        ("ads", ("admob", "applovin", "interstitial", "rewarded", "native ad", "app open")),
        ("firebase", ("firebase", "remote config", "crashlytics", "analytics")),
        ("platform-bridge", ("methodchannel", "setmethodcallhandler", "result.success", "result.error")),
        ("navigation", ("navigate", "navigation", "navcontroller", "nav_graph", "bundle")),
        ("api-network", ("retrofit", "okhttp", "request", "response", "endpoint", "network")),
        ("storage-data", ("database", "room", "repository", "storage", "sharedpreferences", "file")),
        ("lifecycle-ui", ("oncreate", "onresume", "onpause", "ondestroy", "fragment", "activity", "bottomsheet", "dialog", "view")),
        ("state", ("stateflow", "sharedflow", "livedata", "viewmodel", "mutable")),
    ),
)


if __name__ == "__main__":
    run(CONFIG)
