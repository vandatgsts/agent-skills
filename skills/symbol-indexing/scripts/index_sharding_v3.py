#!/usr/bin/env python3
"""Shared v3 semantic sharding and validation for Android and Flutter indexes."""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


POLICY = {
    "root_warn_lines": 500,
    "root_max_lines": 5000,
    "architecture_warn_lines": 400,
    "architecture_max_lines": 600,
    "flow_warn_lines": 400,
    "flow_max_lines": 600,
    "symbol_warn_lines": 800,
    "symbol_max_lines": 1200,
    "symbol_warn_count": 15,
    "symbol_max_count": 20,
    "shard_warn_bytes": 40 * 1024,
    "shard_max_bytes": 64 * 1024,
}

MOJIBAKE = re.compile(r"(?:\ufffd|Ã.|Â.|â(?:†|€|™|œ|ž)|Ä.|Æ.)")
GENERIC_DIRS = {
    "app", "src", "main", "java", "kotlin", "lib", "com", "org", "core",
    "presentation", "domain", "data", "ui", "view", "screen", "screens",
    "feature", "features", "controller", "controllers", "widget", "widgets",
}


@dataclass(frozen=True)
class PlatformConfig:
    key: str
    platform: str
    language: str
    index_candidates: tuple[str, ...]
    symbol_manifest: str
    architecture_dir: str
    symbol_dir: str
    index_schema_v2: str
    symbol_schema_v2: str
    index_schema_v3: str
    symbol_schema_v3: str
    architecture_schema_v3: str
    flow_schema_v3: str
    feature_schema_v3: str
    symbol_shard_schema_v3: str
    route_schema_v3: str
    concern_patterns: tuple[tuple[str, tuple[str, ...]], ...]


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def metrics(value: Any) -> tuple[int, int]:
    text = json_text(value)
    return len(text.splitlines()), len(text.encode("utf-8"))


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as error:
        raise SystemExit(f"Invalid UTF-8: {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise SystemExit(f"Invalid JSON: {path}: {error}") from error


def slug(value: str, fallback: str = "other") -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or fallback


def normalized_path(value: str) -> str:
    return value.replace("\\", "/")


def resolve_index_path(root: Path, config: PlatformConfig) -> Path:
    for candidate in config.index_candidates:
        path = root / candidate
        if path.exists():
            return path
    raise SystemExit(f"Missing {config.key} architecture index; tried: {config.index_candidates}")


def resolve_declared(root: Path, value: str) -> Path:
    normalized = normalized_path(value)
    path = root / normalized
    if path.exists():
        return path
    candidate = root / ".ai" / "indexes" / normalized
    if candidate.exists():
        return candidate
    candidate2 = root / ".ai" / "indexes" / "symbols" / normalized
    if candidate2.exists():
        return candidate2
    raise SystemExit(f"Declared index file does not exist: {value}")


def feature_for_path(path: str, item: dict[str, Any]) -> str:
    explicit = item.get("feature") or item.get("module")
    related = item.get("related_features") or []
    if not explicit and related:
        explicit = related[0]
    if explicit:
        return slug(str(explicit))

    normalized = f"/{normalized_path(path).lower().strip('/')}"
    for marker in ("/features/", "/feature/", "/screens/", "/screen/"):
        if marker in normalized:
            tail = normalized.split(marker, 1)[1].split("/", 1)[0]
            if tail:
                return f"feature-{slug(tail)}"
    if any(token in normalized for token in ("/admob/", "/applovin/", "/ads/")):
        return "infrastructure-ads"
    if any(token in normalized for token in ("billing", "purchase", "subscription")):
        return "infrastructure-billing"
    if any(token in normalized for token in ("navigation", "mainactivity", "routes")):
        return "infrastructure-navigation"
    if any(token in normalized for token in ("database", "repository", "/data/")):
        return "data"
    layer = str(item.get("layer", "")).strip()
    if layer:
        return slug(layer)

    parts = [part for part in normalized.split("/")[:-1] if part and part not in GENERIC_DIRS]
    return slug(parts[-1] if parts else "core")


def search_text(item: dict[str, Any]) -> str:
    fields = [
        item.get("name"), item.get("qualified_name"), item.get("owner"),
        item.get("type"), item.get("purpose"), item.get("layer"),
        item.get("tags"), item.get("side_effects"), item.get("related_features"),
    ]
    return " ".join(str(value).lower() for value in fields if value)


def concern_for(item: dict[str, Any], config: PlatformConfig, fallback_path: str = "", include_path: bool = True) -> str:
    explicit = item.get("concern") or item.get("sub_feature") or item.get("flow")
    if explicit:
        return slug(str(explicit))
    haystack = search_text(item)
    if include_path:
        haystack += " " + normalized_path(fallback_path).lower()
    for concern, patterns in config.concern_patterns:
        if any(pattern in haystack for pattern in patterns):
            return concern
    owner = item.get("owner")
    if owner and not include_path:
        return slug(str(owner))
    return "general"


def unique_symbol_ids(symbols: list[dict[str, Any]], config: PlatformConfig) -> None:
    counts = Counter(str(item.get("qualified_name") or item.get("name") or "") for item in symbols)
    used: set[str] = set()
    for symbol in symbols:
        qualified = str(symbol.get("qualified_name") or symbol.get("name") or "anonymous")
        base = f"{config.key}::{qualified}"
        if counts[qualified] > 1:
            base += f"@{normalized_path(str(symbol.get('file', '')))}:{symbol.get('start_line', 0)}"
        candidate = base
        number = 2
        while candidate in used:
            candidate = f"{base}#{number}"
            number += 1
        symbol["symbol_id"] = candidate
        used.add(candidate)


def build_payload(schema: str, shard_id: str, records_key: str, records: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
    return {"schema": schema, "id": shard_id, **extra, records_key: records}


def over_limit(kind: str, payload: dict[str, Any], hard: bool = False) -> bool:
    lines, size = metrics(payload)
    if hard:
        if size > POLICY["shard_max_bytes"]:
            return True
        if kind == "symbol":
            return lines > POLICY["symbol_max_lines"] or len(payload.get("symbols", [])) > POLICY["symbol_max_count"]
        if kind == "flow":
            return lines > POLICY["flow_max_lines"]
        return lines > POLICY["architecture_max_lines"]
    else:
        if size > POLICY["shard_warn_bytes"]:
            return True
        if kind == "symbol":
            return lines > (POLICY["symbol_warn_lines"] - 50) or len(payload.get("symbols", [])) >= POLICY["symbol_warn_count"]
        if kind == "flow":
            return lines > POLICY["flow_warn_lines"]
        return lines > POLICY["architecture_warn_lines"]


def split_group(
    records: list[dict[str, Any]],
    kind: str,
    schema: str,
    records_key: str,
    base_id: str,
    extra: dict[str, Any] | None = None,
) -> list[tuple[str, list[dict[str, Any]]]]:
    extra = extra or {}
    chunks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for record in records:
        candidate = current + [record]
        probe = build_payload(schema, base_id, records_key, candidate, **extra)
        if current and over_limit(kind, probe, hard=False):
            chunks.append(current)
            current = [record]
            probe = build_payload(schema, base_id, records_key, current, **extra)
        else:
            current = candidate
        if over_limit(kind, probe, hard=True):
            identity = record.get("qualified_name") or record.get("path") or record.get("name") or base_id
            raise SystemExit(f"Single {kind} record exceeds the global hard limit: {identity}")
    if current:
        chunks.append(current)
    suffix = len(chunks) > 1
    return [
        (f"{base_id}--{index:02d}" if suffix else base_id, chunk)
        for index, chunk in enumerate(chunks, start=1)
    ]


def load_source_data(root: Path, config: PlatformConfig) -> tuple[Path, Path, dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    index_path = resolve_index_path(root, config)
    symbol_path = root / config.symbol_manifest
    architecture = load_json(index_path)
    symbol_manifest = load_json(symbol_path)
    files: list[dict[str, Any]] = []
    flows: list[dict[str, Any]] = []
    features: list[dict[str, Any]] = []
    symbols: list[dict[str, Any]] = []

    schema = architecture.get("schema", "")
    if schema == config.index_schema_v3:
        for entry in architecture.get("architecture_shards", []):
            files.extend(load_json(resolve_declared(root, entry["path"])).get("files", []))
        for entry in architecture.get("flow_shards", []):
            flows.extend(load_json(resolve_declared(root, entry["path"])).get("flows", []))
        for entry in architecture.get("feature_shards", []):
            features.extend(load_json(resolve_declared(root, entry["path"])).get("features", []))
    elif schema in (config.index_schema_v2, "flutter-index-manifest-v2", "android-index-manifest-v2"):
        for entry in architecture.get("shards", []):
            target = entry.get("architecture") or entry.get("path")
            if target:
                files.extend(load_json(resolve_declared(root, target)).get("files", []))
        flows.extend(architecture.get("flows", []))
        features.extend(architecture.get("features", []))
    else:
        files.extend(architecture.get("files", []))
        flows.extend(architecture.get("flows", []))
        features.extend(architecture.get("features", []))

    symbol_schema = symbol_manifest.get("schema", "")
    if symbol_schema in (config.symbol_schema_v2, config.symbol_schema_v3, "flutter-symbol-manifest-v2", "flutter-symbol-index-manifest-v2", "android-symbol-manifest-v2", "android-symbol-index-manifest-v2"):
        for entry in symbol_manifest.get("shards", []):
            target = entry.get("path") or entry.get("symbols")
            if target:
                symbols.extend(load_json(resolve_declared(root, target)).get("symbols", []))
    else:
        symbols.extend(symbol_manifest.get("symbols", []))
    return index_path, symbol_path, architecture, symbol_manifest, files, flows, features, symbols


def refs_from(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        ref = value.get("symbol_ref") or value.get("qualified_name") or value.get("symbol")
        if isinstance(ref, str):
            yield ref
    elif isinstance(value, list):
        for item in value:
            yield from refs_from(item)


def enrich_flow_refs(value: Any, by_qualified: dict[str, list[dict[str, Any]]]) -> None:
    if isinstance(value, dict):
        legacy = value.get("symbol")
        if isinstance(legacy, str) and len(by_qualified.get(legacy, [])) == 1:
            target = by_qualified[legacy][0]
            value["symbol_ref"] = target["symbol_id"]
            value["shard_ref"] = target["shard_ref"]
        for child in value.values():
            enrich_flow_refs(child, by_qualified)
    elif isinstance(value, list):
        for child in value:
            enrich_flow_refs(child, by_qualified)


def entry(path: Path, root: Path, payload: dict[str, Any], count_key: str, count: int, **extra: Any) -> dict[str, Any]:
    return {
        "id": payload["id"], "path": path.relative_to(root).as_posix(),
        count_key: count, **extra,
    }


def check_mojibake(value: Any, location: str) -> None:
    if isinstance(value, str) and MOJIBAKE.search(value):
        raise SystemExit(f"Possible mojibake in {location}: {value[:100]}")
    if isinstance(value, dict):
        for key, child in value.items():
            check_mojibake(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            check_mojibake(child, f"{location}[{index}]")


def validate_source_records(root: Path, files: list[dict[str, Any]], symbols: list[dict[str, Any]]) -> None:
    file_paths = [normalized_path(str(item.get("path", ""))) for item in files]
    if len(file_paths) != len(set(file_paths)):
        raise SystemExit("Duplicate architecture file record")
    indexed = set(file_paths)
    source_lines: dict[str, int] = {}
    seen_symbols: set[tuple[str, str, int]] = set()
    for path in indexed:
        if not path or not (root / path).is_file():
            raise SystemExit(f"Indexed source path does not exist: {path}")
    for symbol in symbols:
        path = normalized_path(str(symbol.get("file", "")))
        if path not in indexed:
            raise SystemExit(f"Symbol file lacks architecture coverage: {path}")
        key = (str(symbol.get("qualified_name", "")), path, int(symbol.get("start_line", 0) or 0))
        if key in seen_symbols:
            raise SystemExit(f"Duplicate symbol: {key}")
        seen_symbols.add(key)
        start = symbol.get("start_line")
        end = symbol.get("end_line")
        if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start:
            raise SystemExit(f"Invalid line range for {symbol.get('qualified_name')}: {start}-{end}")
        if path not in source_lines:
            source_lines[path] = len((root / path).read_text(encoding="utf-8", errors="strict").splitlines())
        if end > source_lines[path]:
            raise SystemExit(f"Out-of-range symbol {symbol.get('qualified_name')}: {end} > {source_lines[path]}")


def validate_limit(kind: str, payload: dict[str, Any], warnings: list[str]) -> None:
    lines, size = metrics(payload)
    shard_id = payload.get("id", "manifest")
    if kind == "root":
        if lines > POLICY["root_max_lines"]:
            raise SystemExit(f"Root manifest exceeds {POLICY['root_max_lines']} lines: {shard_id} ({lines})")
        if lines > POLICY["root_warn_lines"]:
            warnings.append(f"{shard_id}: root manifest has {lines} lines")
        return
    if size > POLICY["shard_max_bytes"]:
        raise SystemExit(f"Shard exceeds 64 KiB: {shard_id} ({size} bytes)")
    if size > POLICY["shard_warn_bytes"]:
        warnings.append(f"{shard_id}: shard is {size} bytes")
    line_max = POLICY["symbol_max_lines"] if kind == "symbol" else POLICY["flow_max_lines"] if kind == "flow" else POLICY["architecture_max_lines"]
    line_warn = POLICY["symbol_warn_lines"] if kind == "symbol" else POLICY["flow_warn_lines"] if kind == "flow" else POLICY["architecture_warn_lines"]
    if lines > line_max:
        raise SystemExit(f"{kind.title()} shard exceeds {line_max} lines: {shard_id} ({lines})")
    if lines > line_warn:
        warnings.append(f"{shard_id}: {kind} shard has {lines} lines")
    if kind == "symbol":
        count = len(payload.get("symbols", []))
        if count > POLICY["symbol_max_count"]:
            raise SystemExit(f"Symbol shard exceeds {POLICY['symbol_max_count']} symbols: {shard_id} ({count})")
        if count > POLICY["symbol_warn_count"]:
            warnings.append(f"{shard_id}: symbol shard has {count} symbols")


def atomic_replace(outputs: dict[Path, str], stale_roots: list[Path], manifest_paths: set[Path]) -> None:
    temporary: dict[Path, Path] = {}
    try:
        for target, content in outputs.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            temp = target.with_name(f".{target.name}.tmp-{uuid.uuid4().hex}")
            temp.write_text(content, encoding="utf-8")
            temporary[target] = temp
        ordered = [path for path in outputs if path not in manifest_paths] + [path for path in outputs if path in manifest_paths]
        for target in ordered:
            os.replace(temporary[target], target)
        keep = {path.resolve() for path in outputs}
        for stale_root in stale_roots:
            if not stale_root.exists():
                continue
            for stale in stale_root.rglob("*.json"):
                if stale.resolve() not in keep:
                    stale.unlink()
            for directory in sorted((p for p in stale_root.rglob("*") if p.is_dir()), reverse=True):
                if not any(directory.iterdir()):
                    directory.rmdir()
    finally:
        for temp in temporary.values():
            if temp.exists():
                temp.unlink()


def rebalance(root: Path, config: PlatformConfig) -> None:
    index_path, symbol_path, architecture, symbol_manifest, files, flows, features, symbols = load_source_data(root, config)
    files = copy.deepcopy(files)
    flows = copy.deepcopy(flows)
    features = copy.deepcopy(features)
    symbols = copy.deepcopy(symbols)
    validate_source_records(root, files, symbols)
    unique_symbol_ids(symbols, config)

    feature_by_file = {
        normalized_path(str(item.get("path", ""))): feature_for_path(str(item.get("path", "")), item)
        for item in files
    }

    feat_symbols: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for symbol in symbols:
        source_path = normalized_path(str(symbol.get("file", "")))
        feature = feature_by_file.get(source_path, feature_for_path(source_path, symbol))
        feat_symbols[feature].append(symbol)

    architecture_root = root / config.architecture_dir
    symbol_root = root / config.symbol_dir
    outputs: dict[Path, str] = {}
    symbol_payloads: list[tuple[Path, dict[str, Any], str, str]] = []
    for feature, s_list in sorted(feat_symbols.items()):
        s_list.sort(key=lambda item: (concern_for(item, config, str(item.get("file", "")), include_path=True), str(item.get("file", "")), int(item.get("start_line", 0))))
        if len(s_list) <= 20:
            c = concern_for(s_list[0], config, str(s_list[0].get("file", "")), include_path=True)
            for shard_id, chunk in split_group(s_list, "symbol", config.symbol_shard_schema_v3, "symbols", f"{feature}--{c}", {"feature": feature, "concern": c}):
                for symbol in chunk:
                    symbol["shard_ref"] = shard_id
                path = symbol_root / f"{shard_id}.json"
                symbol_payloads.append((path, build_payload(config.symbol_shard_schema_v3, shard_id, "symbols", chunk, feature=feature, concern=c, depends_on=[]), feature, c))
        else:
            c_groups = defaultdict(list)
            for s in s_list:
                c = concern_for(s, config, str(s.get("file", "")), include_path=True)
                c_groups[c].append(s)
            small_concerns = [c for c, items in c_groups.items() if len(items) < 8 and c != "general"]
            if small_concerns and len(c_groups) > 1:
                for sc in small_concerns:
                    c_groups["general"].extend(c_groups.pop(sc))
            for c, c_list in sorted(c_groups.items()):
                for shard_id, chunk in split_group(c_list, "symbol", config.symbol_shard_schema_v3, "symbols", f"{feature}--{c}", {"feature": feature, "concern": c}):
                    for symbol in chunk:
                        symbol["shard_ref"] = shard_id
                    path = symbol_root / f"{shard_id}.json"
                    symbol_payloads.append((path, build_payload(config.symbol_shard_schema_v3, shard_id, "symbols", chunk, feature=feature, concern=c, depends_on=[]), feature, c))

    by_qualified: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for symbol in symbols:
        by_qualified[str(symbol.get("qualified_name", ""))].append(symbol)
    dependency_fields = ("calls", "called_by", "related_symbols", "callbacks")
    symbol_entries: list[dict[str, Any]] = []
    for path, payload, feature, concern in symbol_payloads:
        dependencies: set[str] = set()
        for symbol in payload["symbols"]:
            for field in dependency_fields:
                for ref in refs_from(symbol.get(field, [])):
                    targets = by_qualified.get(ref, [])
                    if len(targets) == 1 and targets[0]["shard_ref"] != payload["id"]:
                        dependencies.add(targets[0]["shard_ref"])
        payload["depends_on"] = sorted(dependencies)
        validate_limit("symbol", payload, [])
        outputs[path] = json_text(payload)
        symbol_entries.append(entry(path, root, payload, "symbol_count", len(payload["symbols"])))

    route_records = [
        {"symbol_id": item["symbol_id"], "qualified_name": item.get("qualified_name", ""), "shard_ref": item["shard_ref"]}
        for item in sorted(symbols, key=lambda value: value["symbol_id"])
    ]
    route_entries: list[dict[str, Any]] = []
    for shard_id, chunk in split_group(route_records, "architecture", config.route_schema_v3, "routes", "symbol-routes"):
        payload = build_payload(config.route_schema_v3, shard_id, "routes", chunk)
        path = symbol_root / "routes" / f"{shard_id}.json"
        validate_limit("architecture", payload, [])
        outputs[path] = json_text(payload)
        route_entries.append(entry(path, root, payload, "route_count", len(chunk)))

    architecture_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in files:
        path = str(item.get("path", ""))
        feature = feature_for_path(path, item)
        architecture_groups[feature].append(item)
    architecture_entries: list[dict[str, Any]] = []
    for feature, records in sorted(architecture_groups.items()):
        base_id = f"architecture--{feature}"
        records.sort(key=lambda item: str(item.get("path", "")))
        for item in records:
            refs = []
            for name in item.get("main_symbols", []):
                targets = by_qualified.get(str(name), [])
                if len(targets) == 1:
                    refs.append({"symbol_ref": targets[0]["symbol_id"], "shard_ref": targets[0]["shard_ref"]})
            if refs:
                item["symbol_refs"] = refs
        for shard_id, chunk in split_group(records, "architecture", config.architecture_schema_v3, "files", base_id, {"feature": feature}):
            payload = build_payload(config.architecture_schema_v3, shard_id, "files", chunk, feature=feature)
            path = architecture_root / f"{shard_id}.json"
            validate_limit("architecture", payload, [])
            outputs[path] = json_text(payload)
            architecture_entries.append(entry(path, root, payload, "file_count", len(chunk), feature=feature))

    for flow in flows:
        enrich_flow_refs(flow, by_qualified)
    flow_entries: list[dict[str, Any]] = []
    for shard_id, chunk in split_group(flows, "flow", config.flow_schema_v3, "flows", "flows"):
        payload = build_payload(config.flow_schema_v3, shard_id, "flows", chunk)
        path = architecture_root / "flows" / f"{shard_id}.json"
        validate_limit("flow", payload, [])
        outputs[path] = json_text(payload)
        flow_entries.append(entry(path, root, payload, "flow_count", len(chunk)))

    norm_features = [
        {"id": slug(f if isinstance(f, str) else str(f.get("id") or f.get("name"))), "name": f if isinstance(f, str) else str(f.get("name") or f.get("id"))}
        for f in features
    ]
    feature_entries: list[dict[str, Any]] = []
    for shard_id, chunk in split_group(norm_features, "architecture", config.feature_schema_v3, "features", "features"):
        payload = build_payload(config.feature_schema_v3, shard_id, "features", chunk)
        path = architecture_root / "features" / f"{shard_id}.json"
        validate_limit("architecture", payload, [])
        outputs[path] = json_text(payload)
        feature_entries.append(entry(path, root, payload, "feature_count", len(chunk)))

    excluded_architecture_keys = {"schema", "files", "flows", "features", "shards", "architecture_shards", "flow_shards", "feature_shards", "sharding_policy", "symbol_manifest"}
    new_architecture = {key: value for key, value in architecture.items() if key not in excluded_architecture_keys}
    new_architecture.update({
        "schema": config.index_schema_v3,
        "sharding_policy": POLICY,
        "symbol_manifest": Path(config.symbol_manifest).as_posix(),
        "architecture_shards": architecture_entries,
        "flow_shards": flow_entries,
        "feature_shards": feature_entries,
    })
    excluded_symbol_keys = {"schema", "symbols", "shards", "route_shards", "sharding_policy"}
    new_symbol_manifest = {key: value for key, value in symbol_manifest.items() if key not in excluded_symbol_keys}
    new_symbol_manifest.update({
        "schema": config.symbol_schema_v3,
        "sharding_policy": POLICY,
        "shards": symbol_entries,
        "route_shards": route_entries,
    })
    warnings: list[str] = []
    validate_limit("root", new_architecture, warnings)
    validate_limit("root", new_symbol_manifest, warnings)
    check_mojibake(new_architecture, index_path.as_posix())
    check_mojibake(new_symbol_manifest, symbol_path.as_posix())
    for path, content in outputs.items():
        check_mojibake(json.loads(content), path.as_posix())
    outputs[index_path] = json_text(new_architecture)
    outputs[symbol_path] = json_text(new_symbol_manifest)
    atomic_replace(outputs, [architecture_root, symbol_root], {index_path, symbol_path})
    print(f"Rebalanced to v3: {len(architecture_entries)} architecture, {len(flow_entries)} flow, {len(feature_entries)} feature, {len(symbol_entries)} symbol, {len(route_entries)} route shards")
    for warning in warnings:
        print(f"Warning: {warning}")


def validate(root: Path, config: PlatformConfig) -> None:
    index_path, symbol_path, architecture, symbol_manifest, files, flows, features, symbols = load_source_data(root, config)
    warnings: list[str] = []
    check_mojibake(architecture, index_path.as_posix())
    check_mojibake(symbol_manifest, symbol_path.as_posix())
    validate_limit("root", architecture, warnings)
    validate_limit("root", symbol_manifest, warnings)
    validate_source_records(root, files, symbols)

    schema = architecture.get("schema", "")
    symbol_schema = symbol_manifest.get("schema", "")
    if schema not in (config.index_schema_v2, config.index_schema_v3) and "files" not in architecture:
        raise SystemExit(f"Unsupported architecture schema: {schema}")
    if symbol_schema not in (config.symbol_schema_v2, config.symbol_schema_v3) and "symbols" not in symbol_manifest:
        raise SystemExit(f"Unsupported symbol schema: {symbol_schema}")

    shard_ids: set[str] = set()
    if schema == config.index_schema_v3:
        for kind, key, record_key, count_key in (
            ("architecture", "architecture_shards", "files", "file_count"),
            ("flow", "flow_shards", "flows", "flow_count"),
            ("architecture", "feature_shards", "features", "feature_count"),
        ):
            for declared in architecture.get(key, []):
                payload = load_json(resolve_declared(root, declared["path"]))
                if payload.get("id") != declared.get("id") or declared["id"] in shard_ids:
                    raise SystemExit(f"Duplicate or mismatched shard ID: {declared.get('id')}")
                shard_ids.add(declared["id"])
                if len(payload.get(record_key, [])) != declared.get(count_key):
                    raise SystemExit(f"Count mismatch: {declared['id']}")
                validate_limit(kind, payload, warnings)
                check_mojibake(payload, declared["path"])

    symbol_ids: set[str] = set()
    symbol_shard_ids: set[str] = set()
    if symbol_schema == config.symbol_schema_v3:
        for declared in symbol_manifest.get("shards", []):
            payload = load_json(resolve_declared(root, declared["path"]))
            shard_id = declared.get("id")
            if payload.get("id") != shard_id or shard_id in symbol_shard_ids:
                raise SystemExit(f"Duplicate or mismatched symbol shard ID: {shard_id}")
            symbol_shard_ids.add(shard_id)
            if len(payload.get("symbols", [])) != declared.get("symbol_count"):
                raise SystemExit(f"Symbol count mismatch: {shard_id}")
            validate_limit("symbol", payload, warnings)
            check_mojibake(payload, declared["path"])
            for symbol in payload.get("symbols", []):
                symbol_id = symbol.get("symbol_id")
                if not symbol_id or symbol_id in symbol_ids:
                    raise SystemExit(f"Missing or duplicate symbol_id: {symbol_id}")
                if symbol.get("shard_ref") != shard_id:
                    raise SystemExit(f"Invalid shard_ref for {symbol_id}")
                symbol_ids.add(symbol_id)
            for dependency in payload.get("depends_on", []):
                if dependency == shard_id:
                    raise SystemExit(f"Self dependency in {shard_id}")
        for declared in symbol_manifest.get("route_shards", []):
            payload = load_json(resolve_declared(root, declared["path"]))
            validate_limit("architecture", payload, warnings)
            for route in payload.get("routes", []):
                if route.get("symbol_id") not in symbol_ids or route.get("shard_ref") not in symbol_shard_ids:
                    raise SystemExit(f"Unresolved symbol route: {route}")
        for declared in symbol_manifest.get("shards", []):
            payload = load_json(resolve_declared(root, declared["path"]))
            for dependency in payload.get("depends_on", []):
                if dependency not in symbol_shard_ids:
                    raise SystemExit(f"Unresolved depends_on from {declared['id']}: {dependency}")
        for record in [*files, *flows, *features]:
            for ref in explicit_refs(record):
                if ref[0] not in symbol_ids or ref[1] not in symbol_shard_ids:
                    raise SystemExit(f"Unresolved explicit symbol reference: {ref}")
    else:
        # Apply hard limits to v2 as well; --rebalance is the migration path.
        for declared in architecture.get("shards", []):
            arch_target = declared.get("architecture") or declared.get("path")
            if arch_target:
                validate_limit("architecture", load_json(resolve_declared(root, arch_target)), warnings)
        for declared in symbol_manifest.get("shards", []):
            sym_target = declared.get("symbols") or declared.get("path")
            if sym_target:
                validate_limit("symbol", load_json(resolve_declared(root, sym_target)), warnings)

    print(f"Valid: schema={schema or 'legacy'}, {len(files)} files, {len(symbols)} symbols, {len(flows)} flows, {len(features)} features")
    for warning in warnings:
        print(f"Warning: {warning}")


def explicit_refs(value: Any) -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        if "symbol_ref" in value or "shard_ref" in value:
            yield str(value.get("symbol_ref", "")), str(value.get("shard_ref", ""))
        for child in value.values():
            yield from explicit_refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from explicit_refs(child)


def run(config: PlatformConfig) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--rebalance", action="store_true")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.rebalance:
        rebalance(root, config)
    if args.validate:
        validate(root, config)
    if not args.rebalance and not args.validate:
        parser.error("use --rebalance and/or --validate")
