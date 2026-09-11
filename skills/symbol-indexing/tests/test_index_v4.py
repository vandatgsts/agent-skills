from __future__ import annotations

import json
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from index_v4 import (  # noqa: E402
    INDEX_MANIFEST_SCHEMA,
    SYMBOL_MANIFEST_SCHEMA,
    UPDATE_SCHEMA,
    PlatformConfig,
    check_mojibake,
    delete_sources,
    init_index,
    lookup_value,
    recover_pending,
    upsert,
    validate,
)


CONFIG = PlatformConfig(
    key="android",
    platform="android_native",
    language="kotlin/java",
    summary_markdown=".ai/indexes/CODE_INDEX_ANDROID.md",
    index_manifest=".ai/indexes/codeindex_android.json",
    symbol_manifest=".ai/indexes/symbols/android_symbols.json",
    architecture_dir=".ai/indexes/android",
    symbol_dir=".ai/indexes/symbols/android",
    source_globs=("app/src/main/**/*.kt",),
    excludes=("**/generated/**",),
    concern_patterns=(("lifecycle-ui", ("oncreate", "activity")), ("state", ("state",))),
)


class DirectIndexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "app/src/main/java/example/MainActivity.kt"
        self.source.parent.mkdir(parents=True)
        self.source.write_text("\n".join(f"line {index}" for index in range(1, 161)) + "\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_update(self, symbols: list[dict], *, named: bool = False) -> Path:
        payload = {
            "schema": UPDATE_SCHEMA,
            "project_metadata": {"project_name": "Fixture"},
            "sources": [
                {
                    "path": "app/src/main/java/example/MainActivity.kt",
                    "architecture": {
                        "layer": "presentation/activity",
                        "purpose": "Test activity",
                        "related_features": ["launcher"],
                    },
                    "symbols": symbols,
                }
            ],
        }
        if named:
            payload.update(
                {
                    "summary_markdown": "# Fixture Index\n\nLauncher architecture.\n",
                    "flows": [{"id": "startup", "name": "Startup"}],
                    "features": [{"id": "launcher", "name": "Launcher"}],
                    "bridges": [{"id": "launcher-channel", "channel": "launcher/native"}],
                }
            )
        path = self.root / "update.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    @staticmethod
    def symbol(index: int) -> dict:
        return {
            "name": f"onCreate{index}",
            "qualified_name": f"MainActivity.onCreate{index}",
            "type": "lifecycle_method",
            "owner": "MainActivity",
            "signature": f"fun onCreate{index}()",
            "start_line": index + 1,
            "end_line": index + 1,
            "calls": [],
            "called_by": [],
            "reads_state": [],
            "writes_state": [],
            "side_effects": [],
            "related_symbols": [],
            "related_files": [],
            "tags": ["activity"],
            "risks": [],
        }

    def test_direct_upsert_splits_and_validates_without_aggregate_records(self) -> None:
        init_index(self.root, CONFIG, "Fixture")
        upsert(self.root, CONFIG, self.write_update([self.symbol(index) for index in range(25)], named=True))
        validate(self.root, CONFIG)

        index = json.loads((self.root / CONFIG.index_manifest).read_text(encoding="utf-8"))
        symbols = json.loads((self.root / CONFIG.symbol_manifest).read_text(encoding="utf-8"))
        self.assertEqual(INDEX_MANIFEST_SCHEMA, index["schema"])
        self.assertEqual(SYMBOL_MANIFEST_SCHEMA, symbols["schema"])
        self.assertNotIn("files", index)
        self.assertNotIn("symbols", symbols)
        self.assertEqual(25, symbols["stats"]["symbol_count"])
        self.assertTrue((self.root / CONFIG.summary_markdown).is_file())
        shards = list((self.root / ".ai/indexes/symbols/android/shards").rglob("*.json"))
        self.assertEqual(2, len(shards))

        qualified = lookup_value(self.root, CONFIG, qualified_name="MainActivity.onCreate1", include_record=True)
        self.assertEqual("MainActivity.onCreate1", qualified["records"][0]["record"]["qualified_name"])
        source = lookup_value(self.root, CONFIG, source="app/src/main/java/example/MainActivity.kt")
        self.assertEqual(25, len(source["symbol_ids"]))

    def test_source_replacement_removes_old_shards_and_routes(self) -> None:
        init_index(self.root, CONFIG, "Fixture")
        upsert(self.root, CONFIG, self.write_update([self.symbol(index) for index in range(25)]))
        old_shards = set((self.root / ".ai/indexes/symbols/android/shards").rglob("*.json"))

        upsert(self.root, CONFIG, self.write_update([self.symbol(1)]))
        validate(self.root, CONFIG)
        new_shards = set((self.root / ".ai/indexes/symbols/android/shards").rglob("*.json"))
        self.assertEqual(1, len(new_shards))
        self.assertTrue(any(path not in new_shards for path in old_shards))
        manifest = json.loads((self.root / CONFIG.symbol_manifest).read_text(encoding="utf-8"))
        self.assertEqual(1, manifest["stats"]["symbol_count"])

    def test_delete_source_removes_owned_index_data(self) -> None:
        init_index(self.root, CONFIG, "Fixture")
        upsert(self.root, CONFIG, self.write_update([self.symbol(1)]))
        self.source.unlink()
        delete_sources(self.root, CONFIG, ["app/src/main/java/example/MainActivity.kt"])
        validate(self.root, CONFIG)
        manifest = json.loads((self.root / CONFIG.symbol_manifest).read_text(encoding="utf-8"))
        self.assertEqual({"source_count": 0, "symbol_count": 0}, manifest["stats"])
        self.assertFalse(list((self.root / ".ai/indexes/symbols/android/shards").rglob("*.json")))

    def test_rejects_non_v4_manifest(self) -> None:
        index = self.root / CONFIG.index_manifest
        symbols = self.root / CONFIG.symbol_manifest
        index.parent.mkdir(parents=True, exist_ok=True)
        symbols.parent.mkdir(parents=True, exist_ok=True)
        index.write_text('{"schema":"unsupported","version":1,"platform":"android_native"}', encoding="utf-8")
        symbols.write_text('{"schema":"unsupported","version":1,"platform":"android_native"}', encoding="utf-8")
        with self.assertRaises(SystemExit):
            validate(self.root, CONFIG)

    def test_mojibake_detection_accepts_unicode_and_rejects_common_corruption(self) -> None:
        check_mojibake("café - tiếng Việt", "valid")
        with self.assertRaises(SystemExit):
            check_mojibake("caf" + chr(0xC3) + chr(0xA9), "broken")
        with self.assertRaises(SystemExit):
            check_mojibake("It" + chr(0xE2) + chr(0x20AC) + chr(0x2122) + "s", "broken")

    def test_duplicate_qualified_name_routes_survive_one_source_deletion(self) -> None:
        second = self.root / "app/src/main/java/example/SecondActivity.kt"
        second.write_text("first\nsecond\nthird\n", encoding="utf-8")
        first_symbol = self.symbol(1)
        second_symbol = self.symbol(1)
        second_symbol["file"] = "app/src/main/java/example/SecondActivity.kt"
        payload = {
            "schema": UPDATE_SCHEMA,
            "sources": [
                {
                    "path": "app/src/main/java/example/MainActivity.kt",
                    "architecture": {"related_features": ["launcher"]},
                    "symbols": [first_symbol],
                },
                {
                    "path": "app/src/main/java/example/SecondActivity.kt",
                    "architecture": {"related_features": ["launcher"]},
                    "symbols": [second_symbol],
                },
            ],
        }
        update = self.root / "duplicate-name-update.json"
        update.write_text(json.dumps(payload), encoding="utf-8")
        init_index(self.root, CONFIG, "Fixture")
        upsert(self.root, CONFIG, update)
        validate(self.root, CONFIG)

        second.unlink()
        delete_sources(self.root, CONFIG, ["app/src/main/java/example/SecondActivity.kt"])
        validate(self.root, CONFIG)
        qualified_files = list((self.root / ".ai/indexes/symbols/android/routes/qualified").glob("*.json"))
        routes = [route for path in qualified_files for route in json.loads(path.read_text(encoding="utf-8"))["qualified_names"]]
        target = next(route for route in routes if route["qualified_name"] == "MainActivity.onCreate1")
        self.assertEqual(1, len(target["targets"]))

    def test_validation_detects_stale_source_hash(self) -> None:
        init_index(self.root, CONFIG, "Fixture")
        upsert(self.root, CONFIG, self.write_update([self.symbol(1)]))
        self.source.write_text(self.source.read_text(encoding="utf-8") + "changed\n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            validate(self.root, CONFIG)

    def test_recovers_a_journaled_atomic_update(self) -> None:
        target = self.root / ".ai/indexes/android/recovered.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("old", encoding="utf-8")
        temporary = target.with_name(".recovered.json.tmp-v4-android-fixture")
        expected = b"new"
        temporary.write_bytes(expected)
        obsolete = self.root / ".ai/indexes/android/obsolete.json"
        obsolete.parent.mkdir(parents=True, exist_ok=True)
        obsolete.write_text("obsolete", encoding="utf-8")
        journal = self.root / ".ai/indexes/.index-v4-transaction-android.json"
        journal.write_text(
            json.dumps(
                {
                    "schema": "code-index-transaction-v4",
                    "platform": "android_native",
                    "entries": [
                        {
                            "target": ".ai/indexes/android/recovered.json",
                            "temporary": ".ai/indexes/android/.recovered.json.tmp-v4-android-fixture",
                            "manifest": False,
                            "sha256": hashlib.sha256(expected).hexdigest(),
                        }
                    ],
                    "deletes": [".ai/indexes/android/obsolete.json"],
                }
            ),
            encoding="utf-8",
        )
        recover_pending(self.root, CONFIG)
        self.assertEqual(expected, target.read_bytes())
        self.assertFalse(obsolete.exists())
        self.assertFalse(journal.exists())

    def test_rejects_tampered_owned_shard_deletion(self) -> None:
        init_index(self.root, CONFIG, "Fixture")
        upsert(self.root, CONFIG, self.write_update([self.symbol(1)]))
        route_file = next((self.root / ".ai/indexes/symbols/android/routes/source").glob("*.json"))
        route_payload = json.loads(route_file.read_text(encoding="utf-8"))
        route_payload["sources"][0]["architecture_shard"]["path"] = "app/src/main/java/example/MainActivity.kt"
        route_file.write_text(json.dumps(route_payload), encoding="utf-8")
        with self.assertRaises(SystemExit):
            delete_sources(self.root, CONFIG, ["app/src/main/java/example/MainActivity.kt"])
        self.assertTrue(self.source.is_file())

    def test_rejects_out_of_scope_source_and_incorrect_hash(self) -> None:
        init_index(self.root, CONFIG, "Fixture")
        update = json.loads(self.write_update([self.symbol(1)]).read_text(encoding="utf-8"))
        update["sources"][0]["source_hash"] = "incorrect"
        bad_hash = self.root / "bad-hash.json"
        bad_hash.write_text(json.dumps(update), encoding="utf-8")
        with self.assertRaises(SystemExit):
            upsert(self.root, CONFIG, bad_hash)

        dart = self.root / "lib/main.dart"
        dart.parent.mkdir(parents=True)
        dart.write_text("void main() {}\n", encoding="utf-8")
        update["sources"][0] = {
            "path": "lib/main.dart",
            "architecture": {"related_features": ["launcher"]},
            "symbols": [],
        }
        outside = self.root / "outside.json"
        outside.write_text(json.dumps(update), encoding="utf-8")
        with self.assertRaises(SystemExit):
            upsert(self.root, CONFIG, outside)


if __name__ == "__main__":
    unittest.main()
