#!/usr/bin/env python3
"""Migrate/validate Android indexes into feature-sized JSON shards."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def shard_for(path: str, layer: str = "") -> str:
    normalized = path.replace("\\", "/").lower()
    marker = "/feature/"
    if marker in normalized:
        tail = normalized.split(marker, 1)[1].split("/")
        return f"feature-{tail[0]}" if tail and tail[0] else "feature-other"
    if any(token in normalized for token in ("/admob/", "/applovin/", "/ironsource/", "/ads/")):
        return "infrastructure-ads"
    if any(token in normalized for token in ("purchase", "billing", "subscription")):
        return "infrastructure-billing"
    if any(token in normalized for token in ("mainactivity", "/navigation/", "nav_graph")):
        return "infrastructure-navigation"
    if "/database/" in normalized or layer == "data":
        return "data"
    if layer:
        return layer.replace("/", "-").replace(" ", "-")
    return "core"


def source_component(path: str) -> str:
    parts = [part for part in path.replace("\\", "/").lower().split("/") if part]
    ignored = {"src", "main", "java", "kotlin", "app", "aivcteam", "aicartoonnew", "com", "core"}
    for part in reversed(parts[:-1]):
        if part not in ignored and not part.endswith((".kt", ".java")):
            return part.replace("_", "-")
    return "misc"


def grouped_shards(files: list[dict], symbols: list[dict]) -> dict[str, tuple[list[dict], list[dict]]]:
    files_by_id = {item.get("path", ""): item for item in files}
    groups: dict[str, list[str]] = defaultdict(list)
    for path, item in files_by_id.items():
        groups[shard_for(path, item.get("layer", ""))].append(path)
    for symbol in symbols:
        path = symbol.get("file", "")
        if path not in files_by_id:
            groups[shard_for(path)].append(path)
    unique_groups = {name: sorted(set(paths)) for name, paths in groups.items()}
    symbols_by_path: dict[str, list[dict]] = defaultdict(list)
    for symbol in symbols:
        symbols_by_path[symbol.get("file", "")].append(symbol)

    result: dict[str, tuple[list[dict], list[dict]]] = {}
    for base, paths in unique_groups.items():
        total_symbols = sum(len(symbols_by_path[path]) for path in paths)
        buckets = defaultdict(list)
        if total_symbols > 200:
            for path in paths:
                buckets[source_component(path)].append(path)
        else:
            buckets[""] = paths
        for component, component_paths in buckets.items():
            # Keep shards deliberately below the documented 200-symbol/200KB ceiling.
            chunk, count, number = [], 0, 1
            for path in component_paths:
                path_count = len(symbols_by_path[path])
                if chunk and count + path_count > 100:
                    shard_id = f"{base}-{component}".rstrip("-") + f"-{number}"
                    result[shard_id] = ([files_by_id[p] for p in chunk if p in files_by_id], [s for p in chunk for s in symbols_by_path[p]])
                    chunk, count, number = [], 0, number + 1
                chunk.append(path)
                count += path_count
            if chunk:
                suffix = f"-{number}" if number > 1 else ""
                shard_id = f"{base}-{component}".rstrip("-") + suffix
                result[shard_id] = ([files_by_id[p] for p in chunk if p in files_by_id], [s for p in chunk for s in symbols_by_path[p]])
    return result


def migrate(root: Path, rebalance: bool = False) -> None:
    architecture_path = root / ".ai" / "indexes" / "codeindex_android.json"
    symbols_path = root / ".ai" / "indexes" / "symbols" / "android_symbols.json"
    architecture = load_json(architecture_path)
    symbols = load_json(symbols_path)
    if architecture.get("schema") == "android-index-manifest-v2" and not rebalance:
        raise SystemExit("Index is already sharded; use --validate.")
    if rebalance:
        files, all_symbols = [], []
        for shard in architecture.get("shards", []):
            files.extend(load_json(root / shard["architecture"]).get("files", []))
            all_symbols.extend(load_json(root / shard["symbols"]).get("symbols", []))
        architecture["files"] = files
        symbols["symbols"] = all_symbols

    groups = grouped_shards(architecture.get("files", []), symbols.get("symbols", []))

    index_root = root / ".ai" / "indexes" / "android"
    symbol_root = root / ".ai" / "indexes" / "symbols" / "android"
    shards = []
    for stale in list(index_root.glob("*.json")) + list(symbol_root.glob("*.json")):
        stale.unlink()
    for shard_id in sorted(groups):
        architecture_files, shard_symbols = groups[shard_id]
        architecture_file = index_root / f"{shard_id}.json"
        symbol_file = symbol_root / f"{shard_id}.json"
        write_json(architecture_file, {
            "schema": "android-architecture-shard-v2",
            "id": shard_id,
            "files": architecture_files,
        })
        write_json(symbol_file, {
            "schema": "android-symbol-shard-v2",
            "id": shard_id,
            "project_name": symbols.get("project_name", architecture.get("project_name", "")),
            "platform": "android_native",
            "language": "kotlin/java",
            "symbols": shard_symbols,
        })
        shards.append({
            "id": shard_id,
            "architecture": architecture_file.relative_to(root).as_posix(),
            "symbols": symbol_file.relative_to(root).as_posix(),
            "file_count": len(architecture_files),
            "symbol_count": len(shard_symbols),
        })

    manifest = {
        "schema": "android-index-manifest-v2",
        "project_name": architecture.get("project_name", ""),
        "platform": "android_native",
        "language": "kotlin/java",
        "architecture": architecture.get("architecture", ""),
        "dependency_injection": architecture.get("dependency_injection", ""),
        "modules": architecture.get("modules", []),
        "entry_points": architecture.get("entry_points", []),
        "method_channels": architecture.get("method_channels", []),
        "ads": architecture.get("ads", []),
        "billing": architecture.get("billing", []),
        "flows": architecture.get("flows", []),
        "important_files": architecture.get("important_files", []),
        "risks": architecture.get("risks", []),
        "shards": shards,
    }
    write_json(architecture_path, manifest)
    write_json(symbols_path, {
        "schema": "android-symbol-manifest-v2",
        "project_name": manifest["project_name"],
        "platform": "android_native",
        "language": "kotlin/java",
        "shards": [{"id": item["id"], "path": item["symbols"], "symbol_count": item["symbol_count"]} for item in shards],
    })


def validate(root: Path) -> None:
    manifest = load_json(root / ".ai" / "indexes" / "codeindex_android.json")
    symbol_manifest = load_json(root / ".ai" / "indexes" / "symbols" / "android_symbols.json")
    if manifest.get("schema") != "android-index-manifest-v2":
        raise SystemExit(".ai/indexes/codeindex_android.json is not an Android v2 manifest")
    if symbol_manifest.get("schema") != "android-symbol-manifest-v2":
        raise SystemExit("android_symbols.json is not an Android symbol v2 manifest")
    seen_paths, seen_symbols = set(), set()
    for shard in manifest.get("shards", []):
        architecture = load_json(root / shard["architecture"])
        symbols = load_json(root / shard["symbols"])
        if architecture.get("id") != shard["id"] or symbols.get("id") != shard["id"]:
            raise SystemExit(f"Shard id mismatch: {shard['id']}")
        for item in architecture.get("files", []):
            if item.get("path") in seen_paths:
                raise SystemExit(f"Duplicate indexed file: {item['path']}")
            seen_paths.add(item.get("path"))
        for symbol in symbols.get("symbols", []):
            key = (symbol.get("qualified_name"), symbol.get("file"), symbol.get("start_line"))
            if key in seen_symbols:
                raise SystemExit(f"Duplicate symbol: {key}")
            seen_symbols.add(key)
    print(f"Valid: {len(manifest['shards'])} shards, {len(seen_paths)} files, {len(seen_symbols)} symbols")


parser = argparse.ArgumentParser()
parser.add_argument("root", type=Path)
parser.add_argument("--validate", action="store_true")
parser.add_argument("--rebalance", action="store_true")
args = parser.parse_args()
validate(args.root) if args.validate else migrate(args.root, args.rebalance)
