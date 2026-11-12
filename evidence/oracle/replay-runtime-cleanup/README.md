# Offline replay shader compilation and audio retirement

Base: `6437bd8b80a51fd3f573bb32fcca6a445b4f04b9`. No Flash, debugger connection,
reference asset/tape change, native capture, or deployment operation.
`production_admitted=false`, `native_parity_proven=false`, `oracle_accepted=false`,
`certified_global_tick=false`, `os_input_join_proven=false`. M0-02 pending.

## Reproduced causes and changes

Godot 4.7.2 official macOS binary (hash in results.json), headless dummy renderer:

- r13 strict log exit 1: passing built-in TEXTURE to sample_zero's sampler argument
  reaches ShaderCompiler's missing custom_samplers mapping. The dummy material
  compiler initializes empty DefaultIdentifierActions. Replaced that function
  with a fragment-scope macro retaining the identical out-of-range zero condition
  and conditional texture lookup. All six arguments are side-effect-free UV
  expressions. Blur weights, integer rounding, shadow interpolation, color
  matrix, and compositing are unchanged. No renderer branch skips a filter.
- r12 strict log exit 1: five audio resources and their playback instances remain
  at immediate exit. Stop marks playback for fade-out/deletion; the mixer removes
  it, then AudioServer.update releases it on the main thread. One process_frame
  is not an audio retirement barrier. The replay test now frees its scene, waits
  for two observed mixer epochs and main-thread cleanup, bounded by a two-second
  deadline that emits an error on timeout. This only runs after writing the
  replay report; it cannot advance or change replay results. It uses public
  get_time_since_last_mix, not a fixed sleep or an invented game tick.

Engine source anchors (tag 4.7.2-stable):
- [shader compiler, built-in sampler forwarding](https://github.com/godotengine/godot/blob/4.7.2-stable/servers/rendering/shader_compiler.cpp#L1310)
- [dummy material compiler initialization](https://github.com/godotengine/godot/blob/4.7.2-stable/servers/rendering/dummy/storage/material_storage.cpp#L39)
- [audio stop and deferred deletion](https://github.com/godotengine/godot/blob/4.7.2-stable/servers/audio/audio_server.cpp#L1289),
  [mixer removal](https://github.com/godotengine/godot/blob/4.7.2-stable/servers/audio/audio_server.cpp#L535),
  [main-thread retirement](https://github.com/godotengine/godot/blob/4.7.2-stable/servers/audio/audio_server.cpp#L1625)

The isolated test compiles the actual shader and starts a real AudioStreamWAV
playback, drops the player/stream references, and requires both weak references
to expire. In temporary minimal projects: original shader fails strict logging;
omitting drain fails the playback-release assertion; corrected test passes.
Raw logs and full replay reports are gzip-compressed without editing; their
uncompressed hashes are in results.json. Earlier development test invocations
had a type-inference error and a wrong ShaderMaterial method call; these were
corrected in the test, not hidden by the log checker.

## Results and limits

| Check | Result |
| --- | --- |
| Isolated original shader / no-drain negatives | exit 1 / 1 |
| Corrected isolated shader + weak-reference retirement | exit 0 |
| r12 strict replay log after fix | exit 0, no resource leak/error |
| r13 strict replay log after fix | exit 0, no shader/resource error |
| r12 and r13 JSON replay results before vs after | equal in full; no changed simulated results |
| r13 body boundaries | 1166/1166 match |
| r13 geometry over whole diagnostic replay | 897 snapshots/actor, x/y/xscale deltas exactly zero |
| r13 Ready+600 comparison | 601/601 frame rows and 1202/1202 geometry rows match |
| r13 complete checkpoint/state acceptance | refused: no native_checkpoint; state rows contain differences only, not actual values |
| r13 RNG / clock | 298/298 exact RNG sequence; clock matches; checkpoint RNG cursor still absent |
| r12 | stops at boundary722/1076: ql 5.33333333333333 vs 5.333333333333333; no tolerance change |
| Full validator r12 / r13 | exit 1 / 1, first reason source_build_provenance_not_clean (body_boundaries) |

An exploratory run of ai_continuous_checkpoint_reference.gd with r13 is retained
as a **failed incompatible fixture pairing**, not a new gameplay defect: that
runner explicitly selects 一护/白哉, whereas r13 is Naruto/一护. It reports missing
frame inventory and a Byakuya versus yihu random consumer mismatch (strict exit
1); no valid checkpoint follows. That runner was not changed. The complete
validator results above use the correctly paired intro_continuous_reference
runner and preserve its refusal.

Headless shader compilation is not GPU rendering, visual parity, audio-output
quality, or native oracle proof. No complete checkpoint acceptance is claimed.
The next offline step is a source-bound, identity-checked checkpoint/report
adapter for the existing r13 diagnostic (actual states and Ready snapshot),
without changing its intervention provenance or granting native acceptance.
GPU pixel comparison and native oracle obligations remain separate.

## Reproduce

Set GODOT to an installed supported Godot executable and ROOT to this worktree.
The recorded binary/version is pinned in results.json; downloaded executables
and caches are not committed.

```sh
python3.11 tools/run_godot_checked.py --log /tmp/shutdown.log -- "$GODOT" --headless --quit-after 120 --log-file /tmp/shutdown-engine.log --path godot -s res://tests/replay_shutdown_test.gd
python3.11 tools/run_godot_checked.py --log /tmp/r13.log -- "$GODOT" --headless --verbose --log-file /tmp/r13-engine.log --path godot -s res://tests/intro_continuous_reference.gd -- "$ROOT/evidence/ai/input-binary-r13/events.jsonl" /tmp/r13.json combat-boundaries
python3.11 tools/probes/validate_ai_continuous_replay.py evidence/ai/input-binary-r13/events.jsonl /tmp/r13.json --horizon 600 --source-build evidence/ai/input-binary-r13/build.json --output /tmp/r13-acceptance.json
```

For r12 replace input-binary-r13 with input-alias-r12 and output paths. Validator
exit 1 is expected and must not be suppressed. Strict logs must exit 0.
The negative isolation used temporary projects with this same test: replace
only flash_filter.gdshader with the base version, or omit only the drain call.
Run each with --quit-after 120 so an assertion cannot leave a process running.

Repository checks (all exit 0):

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest tools.tests.test_ai_continuous_replay tools.tests.test_godot_result
PYTHONDONTWRITEBYTECODE=1 python3.11 tools/verify.py
PYTHONDONTWRITEBYTECODE=1 python3.11 tools/check_handoff.py
git diff --check
```

Official weekly quota: UNKNOWN. No quota claim is derived from old observations.
