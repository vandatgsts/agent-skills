#!/usr/bin/env python3
"""Migrate, semantically shard, and validate Android code indexes."""
from __future__ import annotations

import sys
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[2]
COMMON_SCRIPTS = SKILLS_ROOT / "symbol-indexing" / "scripts"
if not COMMON_SCRIPTS.is_dir():
    raise SystemExit(f"Missing global symbol-indexing scripts: {COMMON_SCRIPTS}")
sys.path.insert(0, str(COMMON_SCRIPTS))

from index_sharding_v3 import PlatformConfig, run  # noqa: E402


CONFIG = PlatformConfig(
    key="android",
    platform="android_native",
    language="kotlin/java",
    index_candidates=(".ai/indexes/codeindex_android.json", "codeindex_android.json"),
    symbol_manifest=".ai/indexes/symbols/android_symbols.json",
    architecture_dir=".ai/indexes/android",
    symbol_dir=".ai/indexes/symbols/android",
    index_schema_v2="android-index-manifest-v2",
    symbol_schema_v2="android-symbol-manifest-v2",
    index_schema_v3="android-index-manifest-v3",
    symbol_schema_v3="android-symbol-manifest-v3",
    architecture_schema_v3="android-architecture-shard-v3",
    flow_schema_v3="android-flow-shard-v3",
    feature_schema_v3="android-feature-shard-v3",
    symbol_shard_schema_v3="android-symbol-shard-v3",
    route_schema_v3="android-symbol-route-shard-v3",
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
