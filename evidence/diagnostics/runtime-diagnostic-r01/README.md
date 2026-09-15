# Runtime diagnostics and replay r01

## Scope

This is a diagnostic aid, not a gameplay feature and not a parity/completion claim. It records runtime facts without changing combat state. The watchdog emits a bounded `suspected_super_pause_stall` incident after ten seconds without observed state progress while global super pause is active; it does not unpause, resume timelines, or clear `bs`. User pause and hidden-page periods are excluded. A progressing long super pause resets the watchdog signature.

The runtime reports the embedded `res://generated/build_metadata.json` identity when present. A sidecar is useful for export verification, but is not treated as the identity of the running PCK. A match-start recipe plus a latest snapshot is not a complete arbitrary-state checkpoint.

## Replay boundary

The fixed Main executor accepts schema v2 fresh-start recipes for versus mode 3 with two non-CPU players, an available base-form fighter/helper roster, a catalog map, complete per-slot input consumption, and complete random/clock tapes starting at index zero. It refuses missing input entries, unsupported/transformed/CPU/user-paused matches, nonzero pre-match consumer offsets, and explicit build/resource identity mismatches. The current executor does not replay AI, CPU decisions, timer tapes, transformed fighters, or user-paused matches.

A missing source or local build/resource identity is reported as `semantic_match_version_unverified`, even when event and snapshot semantics match. The legacy v1 parser can extract timestamps and combat summaries, but v1 logs lack the global tick/input/consumer data needed for exact replay; `fighter.zhanting` is not global pause state. The shell/export CLI behavior is documented in [DIAGNOSTICS_CLI.md](../../../docs/DIAGNOSTICS_CLI.md).

Inputs recorded from ordinary sessions are the dictionaries actually consumed by the player input path. AI actions are represented by their actual action/transition events and random/clock consumer tape, never as fake empty CPU input. The short native fixture uses an explicitly labeled `diagnostic_input_provider` tape; it demonstrates the recorder/executor loop, not OS keyboard injection.

Live random and clock consumers retain a bounded prefix of 4096 records, preserve absolute consumption indices, and count later dropped records. This is not a rolling recent-tape buffer. A log that has dropped required consumer/input events cannot be described as exactly replayable.

## Evidence

- Fresh capture: `/private/tmp/bvn-diagnostics-web-r01/runtime-events-r03.json` (400 fight ticks, 824 events, 800 consumed slot/tick inputs, 5 random records, 0 clock records, and one settled hit). The fixture reaches `fight_started`, then consumes its recorded input tape. It is a controlled Main diagnostic fixture, not browser keyboard input.
- Shell export: `/private/tmp/bvn-diagnostics-web-r01/shell-export-v2-r03.json` was produced by running the production `shell.html` JavaScript through the Node VM bridge harness, using the real Main event stream and build sidecar. The snapshot callback was acknowledged; 824 events and 800 inputs were retained. This tests the real shell export code path, but it is explicitly not a browser capture.
- Replay: `/private/tmp/bvn-diagnostics-web-r01/cli-replay-r03.json` was produced by `tools/analyze_diagnostics.py replay --project /private/tmp/bvn-diagnostics-web-r01/godot`. It reports `exact_match`, `versionVerified=true`, 824/824 events, 800 inputs, 5/5 random records, and no snapshot difference. Embedded `sourceTreeSha256` matches the copied project; the sidecar PCK hash matches the exported PCK. The temporary project uses its local Web export preset (official Godot 4.7.2 template and `tests/*` excluded from the PCK); its entire source tree, including test scripts and the temporary preset, is covered by the embedded source-tree hash. `generated/build_metadata.json` is excluded from its own source hash to avoid self-reference; the post-export sidecar records the PCK hash.
- Web artifacts: build ID `dcbdab001e6f69c8d2698d6b951d1a7924b4902b7c1c8fc43c2400f5db0e9d17`, PCK SHA-256 `a75f2c30fa58a2ffbdd36846fb859fcb2069b929d2bfecf187d2850a03715acb`. Both local entry points were updated with the same ten files (the nine Web export files plus `build-metadata.json`): `http://127.0.0.1:8765/index.html` and `http://127.0.0.1:8765/sakura-roster-qa/index.html`. Previous nine-file Web exports are backed up under `/private/tmp/bvn-diagnostics-web-r01/entry-backups-20260915/`.
- Truncation: `/private/tmp/bvn-diagnostic-main-truncated-r01.json` is refused before simulation because it has 799 of 800 required input records.
- Watchdog: `/private/tmp/bvn-diagnostic-watchdog-r01.log` reports progressing super pause 0 incidents, frozen super pause 1 incident, user pause 0, hidden page 0. Global pause and fighter state remain unchanged by reporting.
- Consumer bounds: `/private/tmp/bvn-diagnostic-consumers-r03.log` reports 5000 reads each for random and clock, 4096 retained prefix records, 904 dropped, and absolute index 5000; offset replay from index 25 consumes through 27.
- Performance: `/private/tmp/bvn-diagnostic-perf-r02.json` compares the same 400-tick controlled tape with diagnostics on/off. Final HP and positions match. Event emission/fan-out took 1.230 s with 823 events (286,076 serialized bytes) versus 1.087 s with diagnostics disabled. This headless measurement includes serialization/signal fan-out but not the JavaScript bridge, and caller-side payload construction occurs in both runs; treat it as a local sample, not a device budget.

Godot 4.7.2 headless runs print environment log-path and macOS CA-certificate warnings here, but the listed smoke processes exit 0 and emit their `*_OK` markers. Scene/resource leak warnings may remain at test exit and are not counted as gameplay parity evidence.

The repository Python suite passes 220 tests. `tools/validate_contracts.py` passes with the existing `/private/tmp/bvn-contracts-venv` (`5` schemas and `5` examples); `tools/check_handoff.py` and `tools/verify.py` pass for the current manifest. The Godot export logs contain the environment's macOS CA certificate and editor-settings write diagnostics; export completed and the artifact hashes were verified. Godot fixture processes also report resource-leak warnings at exit, recorded separately from replay correctness.

## Reproduction

From the repository root (set `GODOT` to the installed Godot 4.7.2 executable):

```sh
"$GODOT" --headless --path godot -s res://tests/diagnostic_match_export_smoke.gd -- /private/tmp/bvn-diagnostic-main.json
"$GODOT" --headless --path godot -s res://tests/diagnostic_replay_smoke.gd -- /private/tmp/bvn-diagnostic-main.json /private/tmp/bvn-diagnostic-replay.json
"$GODOT" --headless --path godot -s res://tests/diagnostic_watchdog_smoke.gd
"$GODOT" --headless --path godot -s res://tests/diagnostic_consumer_bounds_smoke.gd
"$GODOT" --headless --path godot -s res://tests/diagnostic_perf_smoke.gd -- /private/tmp/bvn-diagnostic-main.json /private/tmp/bvn-diagnostic-perf.json
```

The updated event normalization is covered by a focused Godot test. Browser-side download delivery and a user's real keyboard session remain unverified: the desktop browser was unavailable during this run. The shell bridge validation above uses the production shell implementation with real runtime data but does not claim browser UI acceptance.
