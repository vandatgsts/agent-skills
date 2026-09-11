#!/usr/bin/env python3
"""Direct, source-owned code index storage for Android and Flutter."""
from __future__ import annotations

import argparse
import copy
import fnmatch
import hashlib
import json
import os
import re
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


INDEX_MANIFEST_SCHEMA = "code-index-manifest-v4"
SYMBOL_MANIFEST_SCHEMA = "code-symbol-manifest-v4"
UPDATE_SCHEMA = "code-index-update-v4"
ARCHITECTURE_SHARD_SCHEMA = "code-architecture-shard-v4"
SYMBOL_SHARD_SCHEMA = "code-symbol-shard-v4"
FLOW_SHARD_SCHEMA = "code-flow-shard-v4"
FEATURE_SHARD_SCHEMA = "code-feature-shard-v4"
BRIDGE_SHARD_SCHEMA = "code-bridge-shard-v4"
SOURCE_ROUTE_SCHEMA = "code-source-route-shard-v4"
SYMBOL_ROUTE_SCHEMA = "code-symbol-route-shard-v4"
QUALIFIED_ROUTE_SCHEMA = "code-qualified-route-shard-v4"
ROUTE_BUCKETS = 256

POLICY = {
    "root_warn_lines": 300,
    "root_max_lines": 500,
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

MOJIBAKE = re.compile(r"(?:\ufffd|Ã[\u0080-\u00ff]|Â[\u0080-\u00ff]|â€)")
GENERIC_DIRS = {
    "app", "src", "main", "java", "kotlin", "lib", "com", "org", "core",
    "presentation", "domain", "data", "ui", "view", "screen", "screens",
    "feature", "features", "controller", "controllers", "widget", "widgets",
}
RESERVED_MANIFEST_KEYS = {
    "schema", "version", "platform", "language", "layout", "stats", "generation", "updated_at",
    "summary_markdown", "index_scope", "symbol_manifest", "index_manifest",
}


@dataclass(frozen=True)
class PlatformConfig:
    key: str
    platform: str
    language: str
    summary_markdown: str
    index_manifest: str
    symbol_manifest: str
    architecture_dir: str
    symbol_dir: str
    source_globs: tuple[str, ...]
    excludes: tuple[str, ...]
    concern_patterns: tuple[tuple[str, tuple[str, ...]], ...]
    scope_level: str = "full"


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SystemExit(f"Cannot read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise SystemExit(f"Expected JSON object: {path}")
    return value


def normalized_path(value: str) -> str:
    value = value.replace("\\", "/").strip()
    while value.startswith("./"):
        value = value[2:]
    return value.strip("/")


def slug(value: str, fallback: str = "other") -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return result or fallback


def digest(value: str, length: int = 16) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve_inside(root: Path, relative: str) -> Path:
    relative = normalized_path(relative)
    if not relative:
        raise SystemExit("Empty relative path")
    result = (root / relative).resolve()
    try:
        result.relative_to(root.resolve())
    except ValueError as error:
        raise SystemExit(f"Path escapes project root: {relative}") from error
    return result


def path_ref(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def canonical_source(root: Path, value: str) -> str:
    return path_ref(resolve_inside(root, value), root)


def metrics(value: Any) -> tuple[int, int]:
    encoded = json_text(value).encode("utf-8")
    return encoded.count(b"\n"), len(encoded)


def check_mojibake(value: Any, location: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            check_mojibake(key, location)
            check_mojibake(item, location)
    elif isinstance(value, list):
        for item in value:
            check_mojibake(item, location)
    elif isinstance(value, str) and MOJIBAKE.search(value):
        raise SystemExit(f"Possible mojibake in {location}: {value[:80]}")


def validate_limit(kind: str, payload: dict[str, Any], warnings: list[str] | None = None) -> None:
    warnings = warnings if warnings is not None else []
    lines, size = metrics(payload)
    label = str(payload.get("id") or payload.get("schema") or "payload")
    if kind == "root":
        if lines > POLICY["root_max_lines"]:
            raise SystemExit(f"Root manifest exceeds {POLICY['root_max_lines']} lines: {label} ({lines})")
        if lines > POLICY["root_warn_lines"]:
            warnings.append(f"{label}: root manifest has {lines} lines")
        return
    if size > POLICY["shard_max_bytes"]:
        raise SystemExit(f"Shard exceeds {POLICY['shard_max_bytes']} bytes: {label} ({size})")
    if size > POLICY["shard_warn_bytes"]:
        warnings.append(f"{label}: shard has {size} bytes")
    line_max = POLICY["symbol_max_lines"] if kind == "symbol" else POLICY["flow_max_lines"] if kind == "flow" else POLICY["architecture_max_lines"]
    line_warn = POLICY["symbol_warn_lines"] if kind == "symbol" else POLICY["flow_warn_lines"] if kind == "flow" else POLICY["architecture_warn_lines"]
    if lines > line_max:
        raise SystemExit(f"{kind.title()} shard exceeds {line_max} lines: {label} ({lines})")
    if lines > line_warn:
        warnings.append(f"{label}: {kind} shard has {lines} lines")
    if kind == "symbol":
        count = len(payload.get("symbols", []))
        if count > POLICY["symbol_max_count"]:
            raise SystemExit(f"Symbol shard exceeds {POLICY['symbol_max_count']} symbols: {label} ({count})")
        if count > POLICY["symbol_warn_count"]:
            warnings.append(f"{label}: symbol shard has {count} symbols")


def module_for_path(path: str, architecture: dict[str, Any]) -> str:
    if architecture.get("module"):
        return slug(str(architecture["module"]))
    parts = normalized_path(path).split("/")
    if len(parts) > 1 and parts[0] == "modules":
        return slug(parts[1])
    return slug(parts[0] if parts else "app")


def feature_for_path(path: str, item: dict[str, Any]) -> str:
    related = item.get("related_features")
    if isinstance(related, list) and related:
        return slug(str(related[0]))
    if item.get("feature"):
        return slug(str(item["feature"]))
    parts = [part for part in normalized_path(path).split("/") if part.lower() not in GENERIC_DIRS]
    for marker in ("features", "feature"):
        raw = normalized_path(path).split("/")
        if marker in raw and raw.index(marker) + 1 < len(raw):
            return slug(raw[raw.index(marker) + 1])
    return slug(parts[-2] if len(parts) > 1 else parts[0] if parts else "general")


def semantic_text(value: Any, key: str = "") -> Iterable[str]:
    ignored = {"file", "related_files", "symbol_id", "shard_ref", "platform", "language"}
    if key in ignored:
        return
    if isinstance(value, dict):
        for child_key, child in value.items():
            yield from semantic_text(child, str(child_key))
    elif isinstance(value, list):
        for child in value:
            yield from semantic_text(child, key)
    elif isinstance(value, str):
        yield value


def concern_for(item: dict[str, Any], config: PlatformConfig) -> str:
    searchable = " ".join(semantic_text(item)).lower()
    for concern, patterns in config.concern_patterns:
        if any(pattern.lower() in searchable for pattern in patterns):
            return slug(concern)
    owner = str(item.get("owner") or item.get("name") or item.get("type") or "general")
    return slug(owner)


def source_hash(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise SystemExit(f"Cannot hash source {path}: {error}") from error


def source_in_scope(path: str, config: PlatformConfig) -> bool:
    path = normalized_path(path)
    return any(fnmatch.fnmatch(path, pattern) for pattern in config.source_globs) and not any(
        fnmatch.fnmatch(path, excluded) for excluded in config.excludes
    )


def language_for_source(path: str, config: PlatformConfig) -> str:
    suffix = Path(normalized_path(path)).suffix.lower()
    return {".kt": "kotlin", ".java": "java", ".dart": "dart"}.get(suffix, config.language)


def expected_symbol_id(config: PlatformConfig, source: str, qualified_name: Any, signature: Any) -> str:
    normalized_signature = re.sub(r"\s+", " ", str(signature)).strip()
    identity = "\0".join((config.platform, source, str(qualified_name), normalized_signature))
    return f"{config.key}-{digest(identity, 24)}"


def manifest_layout(config: PlatformConfig) -> dict[str, Any]:
    architecture = normalized_path(config.architecture_dir)
    symbols = normalized_path(config.symbol_dir)
    return {
        "strategy": "source-owned-semantic-shards",
        "architecture_shards": f"{architecture}/architecture",
        "flow_shards": f"{architecture}/flows",
        "feature_shards": f"{architecture}/features",
        "bridge_shards": f"{architecture}/bridges",
        "symbol_shards": f"{symbols}/shards",
        "source_routes": f"{symbols}/routes/source",
        "symbol_routes": f"{symbols}/routes/symbol",
        "qualified_routes": f"{symbols}/routes/qualified",
        "route_buckets": ROUTE_BUCKETS,
    }


def empty_stats() -> dict[str, int]:
    return {"source_count": 0, "file_count": 0, "symbol_count": 0, "flow_count": 0, "feature_count": 0, "bridge_count": 0}


def new_manifests(config: PlatformConfig, project_name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if config.scope_level not in {"full", "boundary", "excluded"}:
        raise SystemExit(f"Unsupported index scope level: {config.scope_level}")
    now = utc_now()
    scope = {"level": config.scope_level, "include": list(config.source_globs), "exclude": list(config.excludes)}
    index = {
        "schema": INDEX_MANIFEST_SCHEMA,
        "version": 4,
        "project_name": project_name,
        "platform": config.platform,
        "language": config.language,
        "generation": 0,
        "updated_at": now,
        "index_scope": scope,
        "layout": manifest_layout(config),
        "summary_markdown": normalized_path(config.summary_markdown),
        "symbol_manifest": normalized_path(config.symbol_manifest),
        "stats": empty_stats(),
    }
    symbols = {
        "schema": SYMBOL_MANIFEST_SCHEMA,
        "version": 4,
        "project_name": project_name,
        "platform": config.platform,
        "language": config.language,
        "generation": 0,
        "updated_at": now,
        "summary_markdown": normalized_path(config.summary_markdown),
        "index_manifest": normalized_path(config.index_manifest),
        "layout": manifest_layout(config),
        "stats": {"source_count": 0, "symbol_count": 0},
    }
    return index, symbols


def manifest_paths(root: Path, config: PlatformConfig) -> tuple[Path, Path]:
    return resolve_inside(root, config.index_manifest), resolve_inside(root, config.symbol_manifest)


def assert_manifest(value: dict[str, Any], schema: str, path: Path, config: PlatformConfig) -> None:
    if value.get("schema") != schema or value.get("version") != 4:
        raise SystemExit(f"Unsupported index schema in {path}; initialize a clean V4 index")
    if value.get("platform") != config.platform:
        raise SystemExit(f"Platform mismatch in {path}: {value.get('platform')}")
    if value.get("language") != config.language:
        raise SystemExit(f"Language mismatch in {path}: {value.get('language')}")
    if value.get("layout") != manifest_layout(config):
        raise SystemExit(f"Layout mismatch in {path}")
    if value.get("summary_markdown") != normalized_path(config.summary_markdown):
        raise SystemExit(f"Summary path mismatch in {path}")
    if not isinstance(value.get("generation"), int) or value["generation"] < 0 or not isinstance(value.get("updated_at"), str):
        raise SystemExit(f"Invalid generation metadata in {path}")


def load_manifests(root: Path, config: PlatformConfig) -> tuple[Path, Path, dict[str, Any], dict[str, Any]]:
    recover_pending(root, config)
    index_path, symbol_path = manifest_paths(root, config)
    if not index_path.exists() or not symbol_path.exists():
        raise SystemExit("V4 manifests are missing; run init first")
    index = load_json(index_path)
    symbols = load_json(symbol_path)
    assert_manifest(index, INDEX_MANIFEST_SCHEMA, index_path, config)
    assert_manifest(symbols, SYMBOL_MANIFEST_SCHEMA, symbol_path, config)
    if index.get("symbol_manifest") != normalized_path(config.symbol_manifest):
        raise SystemExit(f"Paired symbol manifest mismatch in {index_path}")
    if symbols.get("index_manifest") != normalized_path(config.index_manifest):
        raise SystemExit(f"Paired architecture manifest mismatch in {symbol_path}")
    if index.get("generation") != symbols.get("generation"):
        raise SystemExit("Paired manifest generations do not match")
    expected_scope = {"level": config.scope_level, "include": list(config.source_globs), "exclude": list(config.excludes)}
    if index.get("index_scope") != expected_scope:
        raise SystemExit(f"Index scope mismatch in {index_path}")
    return index_path, symbol_path, index, symbols


def load_summary(root: Path, config: PlatformConfig) -> str:
    summary_path = resolve_inside(root, config.summary_markdown)
    if not summary_path.is_file():
        raise SystemExit(f"Missing index summary: {config.summary_markdown}")
    try:
        summary = summary_path.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError) as error:
        raise SystemExit(f"Cannot read index summary {summary_path}: {error}") from error
    if not summary.strip() or not summary.lstrip().startswith("#"):
        raise SystemExit(f"Index summary must be non-empty Markdown: {config.summary_markdown}")
    check_mojibake(summary, str(summary_path))
    return summary


def journal_path(root: Path, config: PlatformConfig) -> Path:
    return resolve_inside(root, f".ai/indexes/.index-v4-transaction-{config.key}.json")


@contextmanager
def platform_lock(root: Path, config: PlatformConfig) -> Iterable[None]:
    lock_path = resolve_inside(root, f".ai/indexes/.index-v4-lock-{config.key}")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+b")
    try:
        if lock_path.stat().st_size == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise SystemExit(f"Another {config.platform} index command is running") from error
        yield
    finally:
        try:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        handle.close()


def is_below(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
        return path.resolve() != directory.resolve()
    except ValueError:
        return False


def assert_write_allowed(root: Path, config: PlatformConfig, path: Path) -> None:
    exact = {resolve_inside(root, value) for value in (config.index_manifest, config.symbol_manifest, config.summary_markdown)}
    roots = (resolve_inside(root, config.architecture_dir), resolve_inside(root, config.symbol_dir))
    if path.resolve() not in exact and not any(is_below(path, directory) for directory in roots):
        raise SystemExit(f"Refusing index write outside configured outputs: {path}")


def assert_delete_allowed(root: Path, config: PlatformConfig, path: Path) -> None:
    roots = (resolve_inside(root, config.architecture_dir), resolve_inside(root, config.symbol_dir))
    if path.suffix.lower() != ".json" or not any(is_below(path, directory) for directory in roots):
        raise SystemExit(f"Refusing index deletion outside generated shard roots: {path}")


def cleanup_platform_temps(root: Path, config: PlatformConfig) -> None:
    pattern = f".*.tmp-v4-{config.key}-*"
    for directory in (resolve_inside(root, config.architecture_dir), resolve_inside(root, config.symbol_dir)):
        if directory.is_dir():
            for temporary in directory.rglob(pattern):
                if temporary.is_file():
                    temporary.unlink()
    for value in (config.index_manifest, config.symbol_manifest, config.summary_markdown):
        target = resolve_inside(root, value)
        for temporary in target.parent.glob(f".{target.name}.tmp-v4-{config.key}-*"):
            if temporary.is_file():
                temporary.unlink()


def atomic_text(path: Path, content: str, marker: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-v4-{marker}-{uuid.uuid4().hex}")
    temporary.write_bytes(content.encode("utf-8"))
    os.replace(temporary, path)


def recover_pending(root: Path, config: PlatformConfig) -> None:
    journal = journal_path(root, config)
    if not journal.exists():
        cleanup_platform_temps(root, config)
        return
    data = load_json(journal)
    entries = data.get("entries", [])
    deletes = data.get("deletes", [])
    if data.get("schema") != "code-index-transaction-v4" or data.get("platform") != config.platform:
        raise SystemExit(f"Invalid V4 transaction journal: {journal}")
    if not isinstance(entries, list) or not all(isinstance(item, dict) for item in entries):
        raise SystemExit(f"Invalid V4 transaction entries: {journal}")
    if not isinstance(deletes, list) or not all(isinstance(item, str) for item in deletes):
        raise SystemExit(f"Invalid V4 transaction deletions: {journal}")
    for manifest_pass in (False, True):
        for item in entries:
            if bool(item.get("manifest")) != manifest_pass:
                continue
            target = resolve_inside(root, str(item["target"]))
            temporary = resolve_inside(root, str(item["temporary"]))
            assert_write_allowed(root, config, target)
            expected_prefix = f".{target.name}.tmp-v4-{config.key}-"
            if temporary.parent != target.parent or not temporary.name.startswith(expected_prefix):
                raise SystemExit(f"Invalid V4 transaction temporary path: {temporary}")
            expected_hash = str(item.get("sha256", ""))
            if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
                raise SystemExit(f"Invalid V4 transaction hash for: {target}")
            if temporary.exists():
                if hashlib.sha256(temporary.read_bytes()).hexdigest() != expected_hash:
                    raise SystemExit(f"Corrupt V4 transaction temporary file: {temporary}")
                target.parent.mkdir(parents=True, exist_ok=True)
                os.replace(temporary, target)
            if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != expected_hash:
                raise SystemExit(f"Cannot recover V4 transaction target: {target}")
    for value in deletes:
        target = resolve_inside(root, str(value))
        assert_delete_allowed(root, config, target)
        if target.exists() and target.is_file():
            target.unlink()
    journal.unlink(missing_ok=True)
    cleanup_platform_temps(root, config)


def commit(root: Path, config: PlatformConfig, outputs: dict[Path, Any], deletes: set[Path], manifests: set[Path]) -> None:
    temporary: dict[Path, Path] = {}
    try:
        for target in outputs:
            assert_write_allowed(root, config, target)
        for target in deletes:
            assert_delete_allowed(root, config, target)
        for target, payload in outputs.items():
            check_mojibake(payload, path_ref(target, root))
            target.parent.mkdir(parents=True, exist_ok=True)
            temp = target.with_name(f".{target.name}.tmp-v4-{config.key}-{uuid.uuid4().hex}")
            content = json_text(payload) if isinstance(payload, dict) else str(payload)
            if not content.endswith("\n"):
                content += "\n"
            temp.write_bytes(content.encode("utf-8"))
            temporary[target] = temp
        data = {
            "schema": "code-index-transaction-v4",
            "platform": config.platform,
            "entries": [
                {"target": path_ref(target, root), "temporary": path_ref(temp, root), "manifest": target in manifests}
                for target, temp in temporary.items()
            ],
            "deletes": [path_ref(path, root) for path in sorted(deletes) if path not in outputs],
        }
        for item, temp in zip(data["entries"], temporary.values()):
            item["sha256"] = hashlib.sha256(temp.read_bytes()).hexdigest()
        atomic_text(journal_path(root, config), json_text(data), config.key)
        for manifest_pass in (False, True):
            for target, temp in temporary.items():
                if (target in manifests) == manifest_pass:
                    os.replace(temp, target)
        for target in deletes:
            if target not in outputs and target.exists() and target.is_file():
                target.unlink()
        journal_path(root, config).unlink(missing_ok=True)
    finally:
        if not journal_path(root, config).exists():
            for temp in temporary.values():
                temp.unlink(missing_ok=True)


def init_index(root: Path, config: PlatformConfig, project_name: str) -> None:
    recover_pending(root, config)
    index_path, symbol_path = manifest_paths(root, config)
    if index_path.exists() or symbol_path.exists():
        if not index_path.exists() or not symbol_path.exists():
            raise SystemExit("Only one V4 manifest exists; repair or remove the incomplete index first")
        load_manifests(root, config)
        load_summary(root, config)
        print("V4 index already initialized")
        return
    index, symbols = new_manifests(config, project_name or root.name)
    summary_path = resolve_inside(root, config.summary_markdown)
    summary = f"# {project_name or root.name} Code Index\n\nDirect V4 {config.platform} index.\n"
    validate_limit("root", index)
    validate_limit("root", symbols)
    commit(root, config, {index_path: index, symbol_path: symbols, summary_path: summary}, set(), {index_path, symbol_path})
    print(f"Initialized V4 index for {config.platform}")


def route_bucket_path(root: Path, config: PlatformConfig, kind: str, key: str) -> Path:
    bucket = hashlib.sha256(key.encode("utf-8")).hexdigest()[:2]
    return resolve_inside(root, f"{normalized_path(config.symbol_dir)}/routes/{kind}/{bucket}.json")


ROUTE_META = {
    "source": (SOURCE_ROUTE_SCHEMA, "sources"),
    "symbol": (SYMBOL_ROUTE_SCHEMA, "symbols"),
    "qualified": (QUALIFIED_ROUTE_SCHEMA, "qualified_names"),
}


def route_payload(kind: str, bucket: str, config: PlatformConfig) -> dict[str, Any]:
    schema, records_key = ROUTE_META[kind]
    return {"schema": schema, "id": f"{kind}-routes-{bucket}", "platform": config.platform, "bucket": bucket, records_key: []}


def load_route(cache: dict[Path, dict[str, Any]], root: Path, config: PlatformConfig, kind: str, key: str) -> tuple[Path, dict[str, Any]]:
    path = route_bucket_path(root, config, kind, key)
    if path not in cache:
        cache[path] = load_json(path) if path.exists() else route_payload(kind, path.stem, config)
        expected, _ = ROUTE_META[kind]
        if cache[path].get("schema") != expected or cache[path].get("platform") != config.platform:
            raise SystemExit(f"Invalid {kind} route schema: {path}")
    return path, cache[path]


def find_record(records: list[dict[str, Any]], key: str, value: str) -> dict[str, Any] | None:
    return next((record for record in records if str(record.get(key)) == value), None)


def remove_record(records: list[dict[str, Any]], key: str, value: str) -> dict[str, Any] | None:
    for index, record in enumerate(records):
        if str(record.get(key)) == value:
            return records.pop(index)
    return None


def normalize_symbol(raw: dict[str, Any], source: str, config: PlatformConfig, source_line_count: int) -> dict[str, Any]:
    symbol = copy.deepcopy(raw)
    required = ("name", "qualified_name", "type", "signature", "start_line", "end_line")
    missing = [key for key in required if symbol.get(key) in (None, "")]
    if missing:
        raise SystemExit(f"Symbol in {source} is missing: {', '.join(missing)}")
    for key in ("name", "qualified_name", "type", "signature"):
        if not isinstance(symbol[key], str):
            raise SystemExit(f"Symbol field {key} must be a string in {source}")
    start, end = symbol.get("start_line"), symbol.get("end_line")
    if isinstance(start, bool) or isinstance(end, bool) or not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start or end > source_line_count:
        raise SystemExit(f"Invalid line range for {symbol.get('qualified_name')} in {source}: {start}-{end}")
    symbol["file"] = source
    symbol["platform"] = config.platform
    symbol["language"] = language_for_source(source, config)
    for key in ("parameters", "calls", "called_by", "reads_state", "writes_state", "side_effects", "related_symbols", "related_files", "tags", "risks"):
        symbol.setdefault(key, [])
        if not isinstance(symbol[key], list):
            raise SystemExit(f"Symbol field {key} must be an array: {symbol['qualified_name']}")
    symbol.setdefault("owner", "")
    symbol.setdefault("visibility", "")
    symbol.setdefault("is_async", False)
    symbol.setdefault("is_suspend", False)
    symbol.setdefault("return_type", "")
    for key in ("owner", "visibility", "return_type"):
        if not isinstance(symbol[key], str):
            raise SystemExit(f"Symbol field {key} must be a string: {symbol['qualified_name']}")
    for key in ("is_async", "is_suspend"):
        if not isinstance(symbol[key], bool):
            raise SystemExit(f"Symbol field {key} must be boolean: {symbol['qualified_name']}")
    symbol["symbol_id"] = expected_symbol_id(config, source, symbol["qualified_name"], symbol["signature"])
    return symbol


def shard_base(root: Path, config: PlatformConfig, source: str, architecture: dict[str, Any]) -> tuple[str, str, str, str]:
    module = module_for_path(source, architecture)
    feature = feature_for_path(source, architecture)
    source_id = digest(source, 16)
    return module, feature, source_id, f"{module}/{feature}"


def symbol_chunks(symbols: list[dict[str, Any]], source: str, architecture: dict[str, Any], root: Path, config: PlatformConfig) -> list[tuple[Path, dict[str, Any]]]:
    module, feature, source_id, hierarchy = shard_base(root, config, source, architecture)
    groups: dict[str, list[dict[str, Any]]] = {}
    for symbol in symbols:
        groups.setdefault(concern_for(symbol, config), []).append(symbol)
    output: list[tuple[Path, dict[str, Any]]] = []
    for concern, records in sorted(groups.items()):
        records.sort(key=lambda item: (int(item["start_line"]), str(item["qualified_name"]), str(item["symbol_id"])))
        chunks: list[list[dict[str, Any]]] = []
        current: list[dict[str, Any]] = []
        for record in records:
            candidate = current + [record]
            chunk_no = len(chunks) + 1
            shard_id = f"{config.key}:{source_id}:{concern}:{chunk_no:02d}"
            probe_records = copy.deepcopy(candidate)
            for item in probe_records:
                item["shard_ref"] = shard_id
            probe = {"schema": SYMBOL_SHARD_SCHEMA, "id": shard_id, "platform": config.platform, "module": module, "feature": feature, "concern": concern, "source": source, "symbols": probe_records}
            try:
                validate_limit("symbol", probe)
            except SystemExit:
                if not current:
                    raise
                chunks.append(current)
                current = [record]
            else:
                current = candidate
        if current:
            chunks.append(current)
        for index, chunk in enumerate(chunks, 1):
            shard_id = f"{config.key}:{source_id}:{concern}:{index:02d}"
            for symbol in chunk:
                symbol["shard_ref"] = shard_id
            payload = {"schema": SYMBOL_SHARD_SCHEMA, "id": shard_id, "platform": config.platform, "module": module, "feature": feature, "concern": concern, "source": source, "symbols": chunk}
            validate_limit("symbol", payload)
            path = resolve_inside(root, f"{normalized_path(config.symbol_dir)}/shards/{hierarchy}/{concern}/{source_id}-{index:02d}.json")
            output.append((path, payload))
    return output


def architecture_shard(source: str, raw: dict[str, Any], symbols: list[dict[str, Any]], root: Path, config: PlatformConfig) -> tuple[Path, dict[str, Any]]:
    architecture = copy.deepcopy(raw)
    architecture["path"] = source
    architecture["platform"] = config.platform
    architecture["language"] = language_for_source(source, config)
    module, feature, source_id, hierarchy = shard_base(root, config, source, architecture)
    architecture["module"] = module
    architecture["feature"] = feature
    architecture["main_symbols"] = [symbol["qualified_name"] for symbol in symbols]
    payload = {"schema": ARCHITECTURE_SHARD_SCHEMA, "id": f"{config.key}:{source_id}:architecture", "platform": config.platform, "module": module, "feature": feature, "source": source, "files": [architecture]}
    validate_limit("architecture", payload)
    path = resolve_inside(root, f"{normalized_path(config.architecture_dir)}/architecture/{hierarchy}/{source_id}.json")
    return path, payload


def named_path(root: Path, config: PlatformConfig, kind: str, record_id: str) -> Path:
    return resolve_inside(root, f"{normalized_path(config.architecture_dir)}/{kind}s/{digest(record_id, 24)}.json")


NAMED_META = {
    "flow": (FLOW_SHARD_SCHEMA, "flows", "flow_count", "flow"),
    "feature": (FEATURE_SHARD_SCHEMA, "features", "feature_count", "architecture"),
    "bridge": (BRIDGE_SHARD_SCHEMA, "bridges", "bridge_count", "architecture"),
}


def stable_record_id(value: Any, kind: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise SystemExit(f"{kind} record requires a non-empty canonical string id")
    return value


def named_payload(kind: str, record: dict[str, Any], config: PlatformConfig) -> tuple[str, dict[str, Any]]:
    schema, key, _, limit_kind = NAMED_META[kind]
    record = copy.deepcopy(record)
    record_id = stable_record_id(record.get("id"), kind)
    payload = {"schema": schema, "id": f"{config.key}:{kind}:{digest(record_id, 24)}", "platform": config.platform, key: [record]}
    validate_limit(limit_kind, payload)
    return record_id, payload


def route_records(payload: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    return payload[ROUTE_META[kind][1]]


def owned_shard_path(root: Path, config: PlatformConfig, reference: Any, schema: str, source: str, directory: str) -> Path:
    if not isinstance(reference, dict) or not reference.get("id") or not reference.get("path"):
        raise SystemExit(f"Invalid owned shard reference for source: {source}")
    path = resolve_inside(root, str(reference["path"]))
    expected_root = resolve_inside(root, directory)
    if not is_below(path, expected_root) or path.suffix.lower() != ".json":
        raise SystemExit(f"Owned shard escapes configured directory: {path}")
    if not path.is_file():
        raise SystemExit(f"Owned shard is missing: {path}")
    payload = load_json(path)
    if payload.get("schema") != schema or payload.get("id") != reference["id"] or normalized_path(str(payload.get("source", ""))) != source:
        raise SystemExit(f"Owned shard reference mismatch: {path}")
    if payload.get("platform") != config.platform:
        raise SystemExit(f"Owned shard platform mismatch: {path}")
    return path


def remove_source(root: Path, config: PlatformConfig, source: str, cache: dict[Path, dict[str, Any]], outputs: dict[Path, dict[str, Any]], deletes: set[Path]) -> tuple[bool, int]:
    source = canonical_source(root, source)
    source_path, source_bucket = load_route(cache, root, config, "source", source)
    old = remove_record(route_records(source_bucket, "source"), "path", source)
    if not old:
        return False, 0
    outputs[source_path] = source_bucket
    architecture = old.get("architecture_shard", {})
    deletes.add(
        owned_shard_path(
            root,
            config,
            architecture,
            ARCHITECTURE_SHARD_SCHEMA,
            source,
            f"{normalized_path(config.architecture_dir)}/architecture",
        )
    )
    for shard in old.get("symbol_shards", []):
        deletes.add(
            owned_shard_path(
                root,
                config,
                shard,
                SYMBOL_SHARD_SCHEMA,
                source,
                f"{normalized_path(config.symbol_dir)}/shards",
            )
        )
    removed = 0
    for symbol_id in old.get("symbol_ids", []):
        symbol_path, symbol_bucket = load_route(cache, root, config, "symbol", str(symbol_id))
        route = remove_record(route_records(symbol_bucket, "symbol"), "symbol_id", str(symbol_id))
        outputs[symbol_path] = symbol_bucket
        if not route:
            continue
        removed += 1
        qualified = str(route.get("qualified_name", ""))
        qualified_path, qualified_bucket = load_route(cache, root, config, "qualified", qualified)
        named = find_record(route_records(qualified_bucket, "qualified"), "qualified_name", qualified)
        if named:
            named["targets"] = [target for target in named.get("targets", []) if target.get("symbol_id") != symbol_id]
            if not named["targets"]:
                remove_record(route_records(qualified_bucket, "qualified"), "qualified_name", qualified)
        outputs[qualified_path] = qualified_bucket
    return True, removed


def add_source(root: Path, config: PlatformConfig, source_update: dict[str, Any], cache: dict[Path, dict[str, Any]], outputs: dict[Path, dict[str, Any]]) -> int:
    raw_source = normalized_path(str(source_update.get("path", "")))
    if not raw_source:
        raise SystemExit("Each source update requires path")
    source = canonical_source(root, raw_source)
    if not source_in_scope(source, config):
        raise SystemExit(f"Source is outside configured index scope: {source}")
    actual_source = resolve_inside(root, source)
    if not actual_source.is_file():
        raise SystemExit(f"Source does not exist: {source}")
    try:
        line_count = len(actual_source.read_text(encoding="utf-8", errors="strict").splitlines())
    except (OSError, UnicodeError) as error:
        raise SystemExit(f"Cannot read source {source}: {error}") from error
    architecture = source_update.get("architecture")
    if not isinstance(architecture, dict):
        raise SystemExit(f"Source update requires architecture object: {source}")
    raw_symbols = source_update.get("symbols", [])
    if not isinstance(raw_symbols, list) or not all(isinstance(item, dict) for item in raw_symbols):
        raise SystemExit(f"Source symbols must be an array of objects: {source}")
    symbols = [normalize_symbol(item, source, config, line_count) for item in raw_symbols]
    ids = [symbol["symbol_id"] for symbol in symbols]
    if len(ids) != len(set(ids)):
        raise SystemExit(f"Duplicate symbol identity in source update: {source}")
    architecture_path, architecture_payload = architecture_shard(source, architecture, symbols, root, config)
    outputs[architecture_path] = architecture_payload
    symbol_payloads = symbol_chunks(symbols, source, architecture, root, config)
    for path, payload in symbol_payloads:
        outputs[path] = payload
    source_route_path, source_bucket = load_route(cache, root, config, "source", source)
    actual_hash = source_hash(actual_source)
    supplied_hash = source_update.get("source_hash")
    if supplied_hash is not None and str(supplied_hash) != actual_hash:
        raise SystemExit(f"Supplied source_hash does not match source: {source}")
    source_route = {
        "path": source,
        "source_hash": actual_hash,
        "architecture_shard": {"id": architecture_payload["id"], "path": path_ref(architecture_path, root)},
        "symbol_shards": [{"id": payload["id"], "path": path_ref(path, root)} for path, payload in symbol_payloads],
        "symbol_ids": ids,
    }
    route_records(source_bucket, "source").append(source_route)
    route_records(source_bucket, "source").sort(key=lambda item: item["path"])
    outputs[source_route_path] = source_bucket
    by_id = {symbol["symbol_id"]: symbol for symbol in symbols}
    shard_for_id: dict[str, tuple[str, str]] = {}
    for path, payload in symbol_payloads:
        for symbol in payload["symbols"]:
            shard_for_id[symbol["symbol_id"]] = (payload["id"], path_ref(path, root))
    for symbol_id, symbol in by_id.items():
        shard_id, shard_path = shard_for_id[symbol_id]
        symbol_route_path, symbol_bucket = load_route(cache, root, config, "symbol", symbol_id)
        route_records(symbol_bucket, "symbol").append({"symbol_id": symbol_id, "qualified_name": symbol["qualified_name"], "file": source, "shard_ref": shard_id, "shard_path": shard_path})
        route_records(symbol_bucket, "symbol").sort(key=lambda item: item["symbol_id"])
        outputs[symbol_route_path] = symbol_bucket
        qualified = str(symbol["qualified_name"])
        qualified_path, qualified_bucket = load_route(cache, root, config, "qualified", qualified)
        named = find_record(route_records(qualified_bucket, "qualified"), "qualified_name", qualified)
        if not named:
            named = {"qualified_name": qualified, "targets": []}
            route_records(qualified_bucket, "qualified").append(named)
        named["targets"].append({"symbol_id": symbol_id, "file": source, "shard_ref": shard_id, "shard_path": shard_path})
        named["targets"].sort(key=lambda item: (item["file"], item["symbol_id"]))
        route_records(qualified_bucket, "qualified").sort(key=lambda item: item["qualified_name"])
        outputs[qualified_path] = qualified_bucket
    return len(symbols)


def merge_metadata(manifest: dict[str, Any], metadata: dict[str, Any]) -> None:
    for key, value in metadata.items():
        if key not in RESERVED_MANIFEST_KEYS:
            manifest[key] = copy.deepcopy(value)


def update_named(root: Path, config: PlatformConfig, payload: dict[str, Any], outputs: dict[Path, dict[str, Any]], deletes: set[Path], stats: dict[str, int]) -> None:
    for kind in NAMED_META:
        plural = f"{kind}s"
        records = payload.get(plural, [])
        if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
            raise SystemExit(f"{plural} must be an array of objects")
        _, _, count_key, _ = NAMED_META[kind]
        record_ids = [stable_record_id(record.get("id"), kind) for record in records]
        if "" in record_ids or len(record_ids) != len(set(record_ids)):
            raise SystemExit(f"{plural} contain missing or duplicate ids")
        delete_key = f"delete_{kind}_ids"
        raw_delete_ids = payload.get(delete_key, [])
        if not isinstance(raw_delete_ids, list):
            raise SystemExit(f"{delete_key} must be an array")
        delete_id_list = [stable_record_id(record_id, kind) for record_id in raw_delete_ids]
        if len(delete_id_list) != len(set(delete_id_list)):
            raise SystemExit(f"{delete_key} contains duplicate ids")
        delete_ids = set(delete_id_list)
        if set(record_ids) & delete_ids:
            raise SystemExit(f"Cannot upsert and delete the same {kind} id")
        for record in records:
            record_id, shard = named_payload(kind, record, config)
            path = named_path(root, config, kind, record_id)
            if not path.exists() and path not in outputs:
                stats[count_key] += 1
            outputs[path] = shard
            deletes.discard(path)
        for record_id in sorted(delete_ids):
            path = named_path(root, config, kind, record_id)
            if path in outputs:
                outputs.pop(path)
                stats[count_key] -= 1
            elif path.exists():
                stats[count_key] -= 1
            deletes.add(path)


def finalize_routes(cache: dict[Path, dict[str, Any]], outputs: dict[Path, dict[str, Any]], deletes: set[Path]) -> None:
    for path, payload in cache.items():
        kind = path.parent.name
        _, records_key = ROUTE_META[kind]
        records = payload.get(records_key, [])
        if records:
            validate_limit("architecture", payload)
            outputs[path] = payload
            deletes.discard(path)
        else:
            outputs.pop(path, None)
            deletes.add(path)


def upsert(root: Path, config: PlatformConfig, input_path: Path) -> None:
    payload = load_json(input_path)
    if payload.get("schema") != UPDATE_SCHEMA:
        raise SystemExit(f"Input schema must be {UPDATE_SCHEMA}")
    index_path, symbol_path, index, symbol_manifest = load_manifests(root, config)
    outputs: dict[Path, Any] = {}
    deletes: set[Path] = set()
    route_cache: dict[Path, dict[str, Any]] = {}
    stats = copy.deepcopy(index.get("stats") or empty_stats())
    sources = payload.get("sources", [])
    if not isinstance(sources, list) or not all(isinstance(item, dict) for item in sources):
        raise SystemExit("sources must be an array of objects")
    source_updates: dict[str, dict[str, Any]] = {}
    for item in sources:
        raw_source = normalized_path(str(item.get("path", "")))
        source = canonical_source(root, raw_source) if raw_source else ""
        if not source or source in source_updates:
            raise SystemExit(f"Missing or duplicate source update: {source}")
        source_updates[source] = item
    raw_delete_sources = payload.get("delete_sources", [])
    if not isinstance(raw_delete_sources, list) or not all(isinstance(item, str) and item == item.strip() and item for item in raw_delete_sources):
        raise SystemExit("delete_sources must be an array")
    delete_source_set = {canonical_source(root, str(item)) for item in raw_delete_sources}
    if delete_source_set & set(source_updates):
        raise SystemExit("Cannot upsert and delete the same source")
    replacements = delete_source_set | set(source_updates)
    for source in replacements - set(source_updates):
        if config.scope_level == "full" and source_in_scope(source, config) and resolve_inside(root, source).is_file():
            raise SystemExit(f"Cannot delete an existing full-scope source from the index: {source}")
    for source in sorted(replacements):
        existed, removed = remove_source(root, config, source, route_cache, outputs, deletes)
        if existed:
            stats["source_count"] -= 1
            stats["file_count"] -= 1
            stats["symbol_count"] -= removed
    for source, item in sorted(source_updates.items()):
        added = add_source(root, config, item, route_cache, outputs)
        stats["source_count"] += 1
        stats["file_count"] += 1
        stats["symbol_count"] += added
    update_named(root, config, payload, outputs, deletes, stats)
    finalize_routes(route_cache, outputs, deletes)
    metadata = payload.get("project_metadata", {})
    if not isinstance(metadata, dict):
        raise SystemExit("project_metadata must be an object")
    merge_metadata(index, metadata)
    merge_metadata(symbol_manifest, {key: value for key, value in metadata.items() if key in ("project_name", "description")})
    if "summary_markdown" in payload:
        summary = payload["summary_markdown"]
        if not isinstance(summary, str) or not summary.strip():
            raise SystemExit("summary_markdown must be a non-empty string")
        outputs[resolve_inside(root, config.summary_markdown)] = summary
    generation = max(int(index.get("generation", 0)), int(symbol_manifest.get("generation", 0))) + 1
    now = utc_now()
    index.update({"generation": generation, "updated_at": now, "stats": stats})
    symbol_manifest.update({"generation": generation, "updated_at": now, "stats": {"source_count": stats["source_count"], "symbol_count": stats["symbol_count"]}})
    validate_limit("root", index)
    validate_limit("root", symbol_manifest)
    outputs[index_path] = index
    outputs[symbol_path] = symbol_manifest
    for path in outputs:
        deletes.discard(path)
    commit(root, config, outputs, deletes, {index_path, symbol_path})
    print(f"Updated V4 generation {generation}: {len(source_updates)} source replacements, {len(replacements - set(source_updates))} deletions")


def delete_sources(root: Path, config: PlatformConfig, sources: list[str]) -> None:
    temporary = root / f".index-v4-delete-{uuid.uuid4().hex}.json"
    payload = {"schema": UPDATE_SCHEMA, "delete_sources": [canonical_source(root, source) for source in sources]}
    try:
        temporary.write_text(json_text(payload), encoding="utf-8")
        upsert(root, config, temporary)
    finally:
        temporary.unlink(missing_ok=True)


def iter_json(directory: Path) -> Iterable[Path]:
    if directory.is_dir():
        yield from sorted(directory.rglob("*.json"))


def validate_payload_schema(
    path: Path,
    expected: str,
    kind: str,
    config: PlatformConfig | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    payload = load_json(path)
    if payload.get("schema") != expected:
        raise SystemExit(f"Unexpected schema in {path}: {payload.get('schema')}")
    if config is not None and payload.get("platform") != config.platform:
        raise SystemExit(f"Shard platform mismatch in {path}: {payload.get('platform')}")
    check_mojibake(payload, str(path))
    validate_limit(kind, payload, warnings)
    return payload


def discover_sources(root: Path, config: PlatformConfig) -> set[str]:
    found: set[str] = set()
    for pattern in config.source_globs:
        for path in root.glob(pattern):
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            relative = canonical_source(root, relative)
            if not source_in_scope(relative, config):
                continue
            found.add(relative)
    return found


def symbol_record_from_route(root: Path, config: PlatformConfig, route: dict[str, Any]) -> dict[str, Any] | None:
    shard_path = resolve_inside(root, str(route.get("shard_path", "")))
    shard = validate_payload_schema(shard_path, SYMBOL_SHARD_SCHEMA, "symbol", config)
    symbol_id = str(route.get("symbol_id", ""))
    return next((symbol for symbol in shard.get("symbols", []) if symbol.get("symbol_id") == symbol_id), None)


def lookup_value(
    root: Path,
    config: PlatformConfig,
    *,
    source: str | None = None,
    symbol_id: str | None = None,
    qualified_name: str | None = None,
    include_record: bool = False,
) -> Any:
    load_manifests(root, config)
    cache: dict[Path, dict[str, Any]] = {}
    if source is not None:
        source = canonical_source(root, source)
        _, bucket = load_route(cache, root, config, "source", source)
        route = find_record(route_records(bucket, "source"), "path", source)
        if route is None or not include_record:
            return route
        architecture = load_json(resolve_inside(root, str(route["architecture_shard"]["path"])))
        symbol_shards = [load_json(resolve_inside(root, str(item["path"]))) for item in route.get("symbol_shards", [])]
        return {"route": route, "architecture": architecture, "symbol_shards": symbol_shards}
    if symbol_id is not None:
        _, bucket = load_route(cache, root, config, "symbol", symbol_id)
        route = find_record(route_records(bucket, "symbol"), "symbol_id", symbol_id)
        if route is None or not include_record:
            return route
        return {"route": route, "record": symbol_record_from_route(root, config, route)}
    if qualified_name is not None:
        _, bucket = load_route(cache, root, config, "qualified", qualified_name)
        route = find_record(route_records(bucket, "qualified"), "qualified_name", qualified_name)
        if route is None or not include_record:
            return route
        records = []
        for target in route.get("targets", []):
            records.append({"target": target, "record": symbol_record_from_route(root, config, target)})
        return {"route": route, "records": records}
    raise SystemExit("Lookup requires one selector")


def validate(root: Path, config: PlatformConfig) -> None:
    index_path, symbol_path, index, symbol_manifest = load_manifests(root, config)
    warnings: list[str] = []
    validate_limit("root", index, warnings)
    validate_limit("root", symbol_manifest, warnings)
    check_mojibake(index, str(index_path))
    check_mojibake(symbol_manifest, str(symbol_path))
    load_summary(root, config)
    layout = manifest_layout(config)
    source_routes: dict[str, dict[str, Any]] = {}
    for path in iter_json(resolve_inside(root, layout["source_routes"])):
        payload = validate_payload_schema(path, SOURCE_ROUTE_SCHEMA, "architecture", config, warnings)
        if payload.get("bucket") != path.stem or payload.get("id") != f"source-routes-{path.stem}":
            raise SystemExit(f"Source route bucket metadata mismatch: {path}")
        for route in payload.get("sources", []):
            raw_source = normalized_path(str(route.get("path", "")))
            source = canonical_source(root, raw_source) if raw_source else ""
            if not source or source in source_routes:
                raise SystemExit(f"Missing or duplicate source route: {source}")
            if raw_source != source:
                raise SystemExit(f"Source route path is not canonical: {raw_source}")
            if path.resolve() != route_bucket_path(root, config, "source", source):
                raise SystemExit(f"Source route is stored in the wrong bucket: {source}")
            source_routes[source] = route
    symbols: dict[str, dict[str, Any]] = {}
    referenced_architecture: set[str] = set()
    referenced_symbol_shards: set[str] = set()
    for source, route in source_routes.items():
        source_path = resolve_inside(root, source)
        if not source_path.is_file():
            raise SystemExit(f"Indexed source does not exist: {source}")
        if route.get("source_hash") != source_hash(source_path):
            raise SystemExit(f"Indexed source hash is stale: {source}")
        architecture_ref = route.get("architecture_shard", {})
        architecture_path = resolve_inside(root, str(architecture_ref.get("path", "")))
        if not is_below(architecture_path, resolve_inside(root, layout["architecture_shards"])):
            raise SystemExit(f"Architecture shard escapes configured directory: {architecture_path}")
        architecture = validate_payload_schema(architecture_path, ARCHITECTURE_SHARD_SCHEMA, "architecture", config, warnings)
        if architecture.get("id") != architecture_ref.get("id") or architecture.get("source") != source:
            raise SystemExit(f"Architecture route mismatch: {source}")
        files = architecture.get("files", [])
        if len(files) != 1 or normalized_path(str(files[0].get("path", ""))) != source:
            raise SystemExit(f"Architecture source record mismatch: {source}")
        if files[0].get("platform") != config.platform or files[0].get("language") != language_for_source(source, config):
            raise SystemExit(f"Architecture platform/language mismatch: {source}")
        module, feature, source_id, hierarchy = shard_base(root, config, source, files[0])
        expected_architecture_path = resolve_inside(root, f"{layout['architecture_shards']}/{hierarchy}/{source_id}.json")
        if architecture_path != expected_architecture_path or architecture.get("id") != f"{config.key}:{source_id}:architecture" or architecture.get("module") != module or architecture.get("feature") != feature:
            raise SystemExit(f"Architecture deterministic identity mismatch: {source}")
        referenced_architecture.add(path_ref(architecture_path, root))
        line_count = len(source_path.read_text(encoding="utf-8", errors="strict").splitlines())
        route_symbol_ids: set[str] = set()
        declared_symbol_shards = route.get("symbol_shards", [])
        if not isinstance(declared_symbol_shards, list) or len({str(item.get('path', '')) for item in declared_symbol_shards}) != len(declared_symbol_shards):
            raise SystemExit(f"Duplicate or invalid symbol shard routes: {source}")
        for shard_ref in declared_symbol_shards:
            shard_path = resolve_inside(root, str(shard_ref.get("path", "")))
            if not is_below(shard_path, resolve_inside(root, layout["symbol_shards"])):
                raise SystemExit(f"Symbol shard escapes configured directory: {shard_path}")
            shard = validate_payload_schema(shard_path, SYMBOL_SHARD_SCHEMA, "symbol", config, warnings)
            if shard.get("id") != shard_ref.get("id") or shard.get("source") != source:
                raise SystemExit(f"Symbol shard route mismatch: {source}")
            parts = str(shard.get("id", "")).split(":")
            if len(parts) != 4 or parts[0] != config.key or parts[1] != source_id or not re.fullmatch(r"\d{2,}", parts[3]) or parts[3] != f"{int(parts[3]):02d}" or int(parts[3]) < 1:
                raise SystemExit(f"Symbol shard deterministic identity mismatch: {shard_path}")
            concern, chunk = parts[2], parts[3]
            expected_shard_path = resolve_inside(root, f"{layout['symbol_shards']}/{hierarchy}/{concern}/{source_id}-{chunk}.json")
            if shard_path != expected_shard_path or shard.get("module") != module or shard.get("feature") != feature or shard.get("concern") != concern:
                raise SystemExit(f"Symbol shard deterministic path mismatch: {shard_path}")
            referenced_symbol_shards.add(path_ref(shard_path, root))
            for symbol in shard.get("symbols", []):
                symbol_id = str(symbol.get("symbol_id", ""))
                if not symbol_id or symbol_id in symbols:
                    raise SystemExit(f"Missing or duplicate symbol_id: {symbol_id}")
                if symbol.get("shard_ref") != shard.get("id") or normalized_path(str(symbol.get("file", ""))) != source:
                    raise SystemExit(f"Symbol ownership mismatch: {symbol_id}")
                if symbol.get("platform") != config.platform or symbol.get("language") != language_for_source(source, config):
                    raise SystemExit(f"Symbol platform/language mismatch: {symbol_id}")
                if symbol_id != expected_symbol_id(config, source, symbol.get("qualified_name"), symbol.get("signature")):
                    raise SystemExit(f"Symbol deterministic identity mismatch: {symbol_id}")
                if normalize_symbol(symbol, source, config, line_count) != symbol:
                    raise SystemExit(f"Symbol schema mismatch: {symbol_id}")
                start, end = symbol.get("start_line"), symbol.get("end_line")
                if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start or end > line_count:
                    raise SystemExit(f"Invalid line range for {symbol.get('qualified_name')}: {start}-{end}")
                symbols[symbol_id] = {"symbol": symbol, "path": path_ref(shard_path, root)}
                route_symbol_ids.add(symbol_id)
        declared_symbol_ids = route.get("symbol_ids", [])
        if not isinstance(declared_symbol_ids, list) or len(declared_symbol_ids) != len(set(declared_symbol_ids)) or route_symbol_ids != set(declared_symbol_ids):
            raise SystemExit(f"Source symbol route mismatch: {source}")
    all_architecture = {path_ref(path, root) for path in iter_json(resolve_inside(root, layout["architecture_shards"]))}
    all_symbol_shards = {path_ref(path, root) for path in iter_json(resolve_inside(root, layout["symbol_shards"]))}
    if all_architecture != referenced_architecture:
        raise SystemExit("Orphan or missing architecture shard detected")
    if all_symbol_shards != referenced_symbol_shards:
        raise SystemExit("Orphan or missing symbol shard detected")
    symbol_routes: dict[str, dict[str, Any]] = {}
    for path in iter_json(resolve_inside(root, layout["symbol_routes"])):
        payload = validate_payload_schema(path, SYMBOL_ROUTE_SCHEMA, "architecture", config, warnings)
        if payload.get("bucket") != path.stem or payload.get("id") != f"symbol-routes-{path.stem}":
            raise SystemExit(f"Symbol route bucket metadata mismatch: {path}")
        for route in payload.get("symbols", []):
            symbol_id = str(route.get("symbol_id", ""))
            if not symbol_id or symbol_id in symbol_routes:
                raise SystemExit(f"Missing or duplicate symbol route: {symbol_id}")
            if path.resolve() != route_bucket_path(root, config, "symbol", symbol_id):
                raise SystemExit(f"Symbol route is stored in the wrong bucket: {symbol_id}")
            symbol_routes[symbol_id] = route
    if set(symbol_routes) != set(symbols):
        raise SystemExit("Symbol route coverage mismatch")
    expected_qualified: dict[str, dict[str, dict[str, Any]]] = {}
    for symbol_id, value in symbols.items():
        symbol = value["symbol"]
        route = symbol_routes[symbol_id]
        if route.get("qualified_name") != symbol.get("qualified_name") or normalized_path(str(route.get("file", ""))) != normalized_path(str(symbol.get("file", ""))) or route.get("shard_ref") != symbol.get("shard_ref") or route.get("shard_path") != value["path"]:
            raise SystemExit(f"Symbol route mismatch: {symbol_id}")
        expected_qualified.setdefault(str(symbol.get("qualified_name", "")), {})[symbol_id] = {
            "symbol_id": symbol_id,
            "file": symbol["file"],
            "shard_ref": symbol["shard_ref"],
            "shard_path": value["path"],
        }
    actual_qualified: dict[str, dict[str, dict[str, Any]]] = {}
    for path in iter_json(resolve_inside(root, layout["qualified_routes"])):
        payload = validate_payload_schema(path, QUALIFIED_ROUTE_SCHEMA, "architecture", config, warnings)
        if payload.get("bucket") != path.stem or payload.get("id") != f"qualified-routes-{path.stem}":
            raise SystemExit(f"Qualified route bucket metadata mismatch: {path}")
        for route in payload.get("qualified_names", []):
            name = str(route.get("qualified_name", ""))
            if not name or name in actual_qualified:
                raise SystemExit(f"Missing or duplicate qualified route: {name}")
            if path.resolve() != route_bucket_path(root, config, "qualified", name):
                raise SystemExit(f"Qualified route is stored in the wrong bucket: {name}")
            targets = route.get("targets", [])
            if not isinstance(targets, list):
                raise SystemExit(f"Qualified route targets must be an array: {name}")
            by_id = {str(target.get("symbol_id", "")): target for target in targets}
            if "" in by_id or len(by_id) != len(targets):
                raise SystemExit(f"Duplicate or missing qualified route target: {name}")
            actual_qualified[name] = by_id
    if actual_qualified != expected_qualified:
        raise SystemExit("Qualified-name route coverage mismatch")
    counts: dict[str, int] = {}
    for kind, (schema, records_key, count_key, limit_kind) in NAMED_META.items():
        directory = resolve_inside(root, f"{normalized_path(config.architecture_dir)}/{kind}s")
        count = 0
        seen: set[str] = set()
        for path in iter_json(directory):
            shard = validate_payload_schema(path, schema, limit_kind, config, warnings)
            records = shard.get(records_key, [])
            if len(records) != 1:
                raise SystemExit(f"V4 {kind} shard must own exactly one record: {path}")
            record_id = str(records[0].get("id", ""))
            if not record_id or record_id in seen:
                raise SystemExit(f"Missing or duplicate {kind} id: {record_id}")
            if path != named_path(root, config, kind, record_id) or shard.get("id") != f"{config.key}:{kind}:{digest(record_id, 24)}":
                raise SystemExit(f"{kind.title()} deterministic identity mismatch: {path}")
            seen.add(record_id)
            count += 1
        counts[count_key] = count
    actual_stats = {
        "source_count": len(source_routes),
        "file_count": len(source_routes),
        "symbol_count": len(symbols),
        **counts,
    }
    if index.get("stats") != actual_stats:
        raise SystemExit(f"Index stats mismatch: expected {actual_stats}, found {index.get('stats')}")
    if symbol_manifest.get("stats") != {"source_count": len(source_routes), "symbol_count": len(symbols)}:
        raise SystemExit("Symbol manifest stats mismatch")
    if index.get("index_scope", {}).get("level") == "full":
        discovered = discover_sources(root, config)
        if discovered != set(source_routes):
            missing = sorted(discovered - set(source_routes))[:10]
            stale = sorted(set(source_routes) - discovered)[:10]
            raise SystemExit(f"Source coverage mismatch; missing={missing}, stale={stale}")
    print(f"V4 valid: {len(source_routes)} sources, {len(symbols)} symbols, {counts['flow_count']} flows, {counts['feature_count']} features, {counts['bridge_count']} bridges")
    for warning in warnings:
        print(f"Warning: {warning}")


def run(config: PlatformConfig) -> None:
    parser = argparse.ArgumentParser(description=f"Direct V4 index maintenance for {config.platform}")
    parser.add_argument("root", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    init_parser = commands.add_parser("init", help="initialize empty V4 manifests")
    init_parser.add_argument("--project-name", default="")
    upsert_parser = commands.add_parser("upsert", help="replace indexed records for the supplied sources")
    upsert_parser.add_argument("--input", type=Path, required=True)
    delete_parser = commands.add_parser("delete-source", help="remove records owned by source paths")
    delete_parser.add_argument("--file", action="append", required=True)
    lookup_parser = commands.add_parser("lookup", help="resolve a source, symbol ID, or qualified name")
    lookup_group = lookup_parser.add_mutually_exclusive_group(required=True)
    lookup_group.add_argument("--source")
    lookup_group.add_argument("--symbol-id")
    lookup_group.add_argument("--qualified-name")
    lookup_parser.add_argument("--record", action="store_true", help="also load the owning record or shards")
    commands.add_parser("validate", help="validate the complete V4 index")
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        raise SystemExit(f"Project root does not exist: {root}")
    with platform_lock(root, config):
        if args.command == "init":
            init_index(root, config, args.project_name)
        elif args.command == "upsert":
            upsert(root, config, args.input.resolve())
        elif args.command == "delete-source":
            delete_sources(root, config, args.file)
        elif args.command == "lookup":
            result = lookup_value(
                root,
                config,
                source=args.source,
                symbol_id=args.symbol_id,
                qualified_name=args.qualified_name,
                include_record=args.record,
            )
            if result is None:
                raise SystemExit("No matching index route")
            print(json_text(result), end="")
        elif args.command == "validate":
            validate(root, config)


if __name__ == "__main__":
    raise SystemExit("Use a platform wrapper")
