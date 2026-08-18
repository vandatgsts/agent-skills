#!/usr/bin/env python3
"""Migrate, semantically shard, and validate Flutter code indexes."""
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
    key="flutter",
    platform="flutter",
    language="dart",
    index_candidates=(".ai/indexes/codeindex_flutter.json", "codeindex_flutter.json"),
    symbol_manifest=".ai/indexes/symbols/flutter_symbols.json",
    architecture_dir=".ai/indexes/flutter",
    symbol_dir=".ai/indexes/symbols/flutter",
    index_schema_v2="flutter-index-manifest-v2",
    symbol_schema_v2="flutter-symbol-manifest-v2",
    index_schema_v3="flutter-index-manifest-v3",
    symbol_schema_v3="flutter-symbol-manifest-v3",
    architecture_schema_v3="flutter-architecture-shard-v3",
    flow_schema_v3="flutter-flow-shard-v3",
    feature_schema_v3="flutter-feature-shard-v3",
    symbol_shard_schema_v3="flutter-symbol-shard-v3",
    route_schema_v3="flutter-symbol-route-shard-v3",
    concern_patterns=(
        ("generation-processing", ("generate", "processing", "transform", "render", "inference", "filter", "restore", "headshot", "enhance", "swap", "mask", "crop", "brush", "animation", "effect")),
        ("input-picking", ("pickimage", "picker", "camera", "gallery", "input", "album", "photo", "image")),
        ("navigation", ("get.tonamed", "get.off", "navigate", "navigation", "route", "router", "back", "pop", "push")),
        ("preview", ("preview", "thumbnail")),
        ("result", ("result", "output", "download", "share", "export", "save")),
        ("permission", ("permission", "required access", "requestpermission")),
        ("billing", ("billing", "purchase", "subscription", "premium", "iap", "credit", "coin", "payment", "order", "receipt", "sku", "gift")),
        ("ads", ("admob", "applovin", "interstitial", "rewarded", "native ad", "app open", "banner", "ad")),
        ("platform-bridge", ("methodchannel", "eventchannel", "invokemethod", "platform channel", "native_subscription")),
        ("api-network", ("api", "request", "response", "endpoint", "http", "dio", "network", "client", "remote", "config", "firebase", "socket")),
        ("storage-data", ("database", "repository", "storage", "sharedpreferences", "hive", "file", "preference", "cache", "dao", "model", "entity", "dto", "converter", "json", "table", "db", "local")),
        ("lifecycle-ui", ("initstate", "dispose", "oninit", "onready", "onclose", "widget", "screen", "dialog", "bottomsheet", "build", "paint", "canvas", "view", "style", "theme", "color", "icon", "asset", "toast", "sheet", "drawer", "card", "bar", "tile", "item", "row", "column", "text", "button")),
        ("state", ("state", "rx", "controller", "provider", "bloc", "cubit", "riverpod", "manager", "notifier", "store", "event", "action", "mixin", "binding")),
    ),
)


if __name__ == "__main__":
    run(CONFIG)
