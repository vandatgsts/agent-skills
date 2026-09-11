#!/usr/bin/env python3
"""Flutter V4 direct-index wrapper around the shared indexing engine."""
from __future__ import annotations

import sys
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[2]
COMMON_SCRIPTS = SKILLS_ROOT / "symbol-indexing" / "scripts"
if not COMMON_SCRIPTS.is_dir():
    raise SystemExit(f"Missing shared symbol-indexing scripts: {COMMON_SCRIPTS}")
sys.path.insert(0, str(COMMON_SCRIPTS))

from index_v4 import PlatformConfig, run  # noqa: E402


CONFIG = PlatformConfig(
    key="flutter",
    platform="flutter",
    language="dart",
    summary_markdown=".ai/indexes/CODE_INDEX_FLUTTER.md",
    index_manifest=".ai/indexes/codeindex_flutter.json",
    symbol_manifest=".ai/indexes/symbols/flutter_symbols.json",
    architecture_dir=".ai/indexes/flutter",
    symbol_dir=".ai/indexes/symbols/flutter",
    source_globs=("lib/*.dart", "lib/**/*.dart"),
    excludes=(
        "build/**",
        ".dart_tool/**",
        ".idea/**",
        ".vscode/**",
        "**/*.g.dart",
        "**/*.freezed.dart",
        "**/*.gr.dart",
        "android/build/**",
        "ios/Pods/**",
    ),
    concern_patterns=(
        ("platform-bridge", ("methodchannel", "eventchannel", "invokemethod", "setmethodcallhandler")),
        ("navigation", ("route", "get.to", "get.off", "get.offall", "get.tonamed", "navigator")),
        ("generation-processing", ("generate", "processing", "inference", "pipeline")),
        ("input-picking", ("picker", "pickimage", "camera", "gallery", "file_picker")),
        ("preview", ("preview", "thumbnail")),
        ("result", ("result", "output")),
        ("permission", ("permission", "authorization")),
        ("storage-data", ("database", "repository", "storage", "cache", "sharedpreferences")),
        ("api-network", ("api", "http", "dio", "retrofit", "request", "response", "endpoint")),
        ("billing", ("billing", "purchase", "subscription", "premium")),
        ("ads", ("admob", "ads", "rewarded", "interstitial", "banner")),
        ("lifecycle-ui", ("widget", "screen", "page", "build", "initstate", "dispose")),
        ("state", ("controller", "getx", "rx", "obx", "state", "stream", "future")),
    ),
)


if __name__ == "__main__":
    run(CONFIG)
