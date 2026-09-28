# Flat checkpoint dictionary entries (2026-09-28)

## Change

Checkpoint dictionary records now store entries as `[encoded_key, encoded_value, ...]` instead of allocating a two-element Array for every key/value pair. Loading uses stride two. `load_state` validates that the decoded record list is an Array and each dictionary has an even-length entries Array before changing battle state. The local graph build marker is `battle-local-pba-dict-flat-v2`; peers with the older graph layout therefore have a different online build fingerprint.

This changes only the local checkpoint graph representation. Dictionary key iteration order, record order and IDs, key/value encodings, array records, object/node lifetime handling, RNG/timer fields, snapshot fingerprints, and rollback scheduling remain unchanged.

## Evidence

The frozen PBA graph tape contains 331 saves from the existing rollback fixture. The canonical baseline path is `/private/tmp/bvn26-perf-opt-r2/candidate-graphs.txt`. The local comparator first used `baseline-graphs.txt`, but both files have the same SHA-256 (`8f9424453b59a449897297da7c772c2fdf8e08110cee82131c54c70649f266ae`); independent acceptance reran the comparison using the canonical `candidate-graphs.txt` path. The comparison decoded each old and new graph and compared the complete record arrays with `State.first_difference`. For the new format only, each dictionary's flat entries were paired in the original order; no other field or record was normalized or omitted. All 331 frames matched.

Across those saves, the old graph contained 216,602 pair Arrays, or 654.4 per save, which the flat layout removes. Serialized graph bytes fell from 79,496,304 to 77,763,488 bytes: 1,732,816 bytes total, averaging 5,235 bytes (2.18%) per save. The candidate graph reached 569 records. These figures measure serialized graph payload only. A 32-snapshot window at the measured average would contain about 167,523 fewer graph bytes; actual retained memory, object references, and allocator overhead were not measured.

The same delayed-input profile completed on both sources with 10 corrections, 65 replayed frames, and 15 waits. The candidate's `semantic_cross_source_difference` was empty against the frozen complete-state reference. The flat-specific smoke passed shared-reference identity, distinct-but-equal Arrays and Dictionaries, typed empty/nonempty Dictionaries, self-reference decoding, and odd-entry rejection before restoration; after the rejection, the live state still matched.

One sequential candidate/baseline timing pair was collected while the host was heavily loaded. Candidate: step mean 50.71 ms, p95 101.00 ms, encode 8.104 s across 396 saves (20.46 ms/save). Frozen PBA baseline immediately after: step mean 69.44 ms, p95 189.62 ms, encode 12.062 s (30.46 ms/save). The spread is too large to attribute as a stable runtime gain; these timings are observational only. This round makes no frame-rate claim.

An isolated self-referential Dictionary probe emits Godot's `Max recursion reached` engine error in both the frozen PBA source and the candidate because the existing encoder calls `hash(value)` before recording container identity. Both still produce the same single self-reference record. This pre-existing synthetic cycle boundary is not changed or claimed as supported by this layout optimization. The regression checks that the flat graph validator and decoder preserve explicit self-reference records.

## Reproduction

Godot used: `/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot`, 4.7.2 stable.

```sh
/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot --headless --path "$PWD/godot" --log-file /private/tmp/bvn26-perf-opt-r3/flat-dictionary-smoke.log --script res://tests/battle_checkpoint_flat_dictionary_smoke.gd

/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot --headless --path "$PWD/godot" --log-file /private/tmp/bvn26-perf-opt-r3/flat-graph-compare.log --script res://tests/battle_checkpoint_flat_graph_compare.gd -- /private/tmp/bvn26-perf-opt-r2/candidate-graphs.txt

/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot --headless --path "$PWD/godot" --log-file /private/tmp/bvn26-perf-opt-r3/flat-candidate-delayed.log --script res://tests/rollback_delayed_input_profile.gd -- compare-state /private/tmp/bvn26-perf-opt-r2/baseline-canonical-state.bin

/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot --headless --path /private/tmp/bvn26-perf-opt-r3/baseline-godot --log-file /private/tmp/bvn26-perf-opt-r3/flat-baseline-delayed.log --script res://tests/rollback_delayed_input_profile.gd -- compare-state /private/tmp/bvn26-perf-opt-r2/baseline-canonical-state.bin
```

The baseline project is the APFS-frozen accepted PBA source. The graph tape and all run logs remain under `/private/tmp`; the canonical PBA tape SHA-256 is `8f9424453b59a449897297da7c772c2fdf8e08110cee82131c54c70649f266ae`.

## Compatibility and limits

The generated online manifest was regenerated after the marker change. Its build fingerprint is `849bc06497ba2ff622151d65ff2121f6dd809c8c0a5b4a28e01409d038dd64d5`; content fingerprint is `a52c9b9391f280f06bb5b205607fccdf23f9fe3afade41fbaecc003d5bb063e7`. A temporary Web export was made for a browser smoke, with no deployment or commit. The final candidate PCK is `/private/tmp/bvn26-perf-opt-r3/web-output/flat-candidate-verified.pck` (109,123,200 bytes, SHA-256 `00acc2b94ca5e84c7a2073af0f071db853b6539c7aed2a1f76548ae466c9ab79`). Its embedded profiler configuration uses pair ID `checkpoint-flat-dict-r3-20260928`, the build fingerprint above, and the current `battle_checkpoint.gd`, `simulation_state.gd`, `main.gd`, and online manifest SHA-256 values recorded at export. The visible browser page is `http://127.0.0.1:8038/flat-candidate-verified/index.html`.

The first temporary page was rejected as evidence because its reused profiler config still named the PBA baseline `battle_checkpoint.gd` hash. That config was corrected in the staged project and the package re-exported; the source overlay was then restored and all four staged files were verified back to the PBA baseline.

The corrected visible Chrome 153 / Godot 4.7.2 Web burst completed on `user-log-r01`, with 330 measured frames, 90 warmup frames, zero rollback, and 331 checkpoint saves. Its report's pair ID, build fingerprint, and four source-file hashes match the exported candidate metadata. `receive_plus_step_us` mean was 18,814 μs and p95 was 23,900 μs; checkpoint encode was 2,776,300 μs total (8,389 μs/save), pack 564,000 μs (1,704 μs/save), and retention 74,000 μs (223 μs/save). The raw report is `/private/tmp/bvn26-perf-opt-r3/web-burst-candidate.json`, SHA-256 `a04cad650ac9bbde4e1e1572d7583d7c40fbf90dabae59df2fc7aa064e710ee3`. This is a single candidate smoke with no late inputs; it does not establish a speedup or browser rollback performance.

Real two-peer browser performance, 32-state retained heap bytes, and stable low-load timing are not measured here. The 331-frame graph comparison uses the established default fixture, and delayed replay is covered by the existing 330-tick profile.
