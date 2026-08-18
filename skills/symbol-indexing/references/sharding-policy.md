# Global index sharding policy

Apply this policy to every generated or maintained Android and Flutter index. Platform skills may add classification rules, but they must not weaken these limits.

## Scope levels

- `full`: Index architecture plus important symbols, callers/callees, state, side effects, lifecycle, and flows for product code and internally maintained modules.
- `boundary`: Index only public entry points, APIs used by product code, callbacks, side effects, and threading contracts for vendored or rarely modified modules.
- `excluded`: Ignore generated output, build output, caches, samples, and unused vendored internals.
- Promote a boundary package to `full` while diagnosing or modifying its internals. Keep promoted records current afterward.

Record scope rules in the platform manifest under `index_scope`. Coverage validation applies according to the declared level.

## File limits

Measure UTF-8 JSON serialized with two-space indentation and a trailing newline.

| File | Warn | Hard limit |
|---|---:|---:|
| Root manifest | 300 lines | 500 lines |
| Architecture or flow shard | 400 lines | 600 lines |
| Symbol shard | 800 lines or 15 symbols | 1,200 lines or 20 symbols |
| Any shard | 40 KiB | 64 KiB |

Treat any exceeded hard limit as validation failure. Do not minify JSON to evade a line limit. Compact oversized records or split their semantic responsibility. A single record that cannot fit is invalid and must be redesigned.

## Semantic partitioning

Partition in this order:

1. platform
2. module
3. feature
4. sub-feature or flow concern
5. numbered chunk only when one concern still exceeds a hard limit

Prefer names such as `feature-camera--capture`, `feature-camera--detection`, and `feature-camera--duplicate-review`. Do not create opaque `feature-camera-1` chunks until semantic partitioning has been exhausted.

Do not force every symbol from one source file into the same shard. Large screens, controllers, fragments, and view models commonly span several concerns. Store each symbol exactly once in its owning shard.

## Links and identity

- Give every symbol a stable `symbol_id` and an owning `shard_ref`.
- Use `symbol_ref` plus `shard_ref` for explicit cross-shard links.
- Keep `qualified_name` for human lookup and legacy compatibility.
- Declare shard-level `depends_on` links derived from resolved callers, callees, related symbols, flows, routes, and platform bridges.
- Store symbol routes in bounded route shards. Do not grow the root manifest with an unbounded symbol map.
- Never duplicate full symbol metadata to make another shard self-contained.

## Schema compatibility

- Read legacy monolithic indexes and v2 manifests.
- Emit v3 manifests on `--rebalance`.
- Preserve project metadata that is not owned by the sharder.
- Move large flow and feature collections into bounded shards instead of retaining them in the root manifest.
- Never flatten v2 or v3 shards back into a monolithic index.

## Safe rebalance

1. Load all declared source shards.
2. Verify architecture coverage before generating output: every indexed symbol file must have an architecture record.
3. Build all v3 payloads in memory.
4. Validate identity, references, limits, counts, paths, line ranges, and UTF-8 before replacing existing files.
5. Write temporary sibling files, atomically replace targets, then remove only stale generated shards.
6. Run `--validate` after replacement.

Validation must reject:

- missing or duplicate shard IDs
- duplicate symbols or files
- mismatched manifest counts
- unresolved explicit `symbol_ref` or `shard_ref`
- symbols whose source file lacks architecture coverage
- nonexistent source paths
- invalid or out-of-range source line ranges
- malformed UTF-8 or common mojibake sequences
- shards over a hard limit

Warnings must identify shards approaching soft limits and summarize coverage by declared scope.
