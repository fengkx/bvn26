# Flat checkpoint dictionary layout: independent acceptance (2026-09-28)

## Verdict

The flat dictionary-entry layout passes the scoped graph, delayed-input, and native online-pair correctness checks. The full 331-frame graph comparison found no logical record difference after pairing only dictionary `entries` for comparison. The layout removes 216,602 per-entry pair Arrays and reduces serialized graph payload by 2.18%. The available timing runs are too noisy to attribute a speedup. This is not evidence of WebRTC behavior or a real-time 30 Hz pass.

The previous PBA acceptance and the user-run P1/P2 diagnosis remain in [acceptance-r2-2026-09-28.md](acceptance-r2-2026-09-28.md). This report covers only the subsequent dictionary layout change.

## Reviewed identity and representation

The candidate uses graph marker `battle-local-pba-dict-flat-v2`. Its `battle_checkpoint.gd` SHA-256 is `16ebed2dc1fa5fc45f11c61053261db02255ce2474017de76ac0bea7e54f78fc`; `simulation_state.gd` is `847277c7bfd89b58f107b56ad8375b9c774dd2b5e0b3dcd8d29641ffadf683cb`. The frozen PBA baseline files are `192c42ae80014bdbf0b3f576303ea63cdbc9765817735975f23875f031eaa076` and `8d8ee664371b5612b57e625545595d1e6ce12f52f1364fc10c32b66f95122522`, respectively. Godot was 4.7.2 stable.

The candidate stores dictionary entries as `[key, value, ...]` and restores them with a stride of two. Arrays keep their existing record layout. Loading validates the decoded record array and rejects odd dictionary entry counts before unbinding or restoring battle state. The delayed-input comparison accepts only the three known graph markers (old text, PBA, and flat-v2); unknown markers fail. For flat-v2 only, it pairs dictionary entries in their original order, then compares the complete canonical state. No other graph field is dropped or normalized.

## Complete graph comparison

I independently ran the 331-frame comparator against the frozen accepted PBA graph tape. The tape is 331 rows and 158,996,470 text bytes, SHA-256 `8f9424453b59a449897297da7c772c2fdf8e08110cee82131c54c70649f266ae`. Its source checkpoint file has the frozen baseline hash above. Every declared row length matched its decoded bytes; every record kind and record count matched; `State.first_difference` returned empty for the full graph at every frame. Only the flat dictionary representation was paired for comparison.

The result was 216,602 dictionary entries / pair Arrays across 331 saves, about 654.4 per save. Serialized graph payload fell from 79,496,304 to 77,763,488 bytes, saving 1,732,816 bytes (2.18%); the largest graph had 569 records. These are serialized payload figures, not retained heap or allocator measurements. The independent run exited 0; its log is `/private/tmp/bvn26-perf-opt-r3/acceptance-flat-graph-compare.log` (SHA-256 `c4b761e929d75a67684e3eb51c25d2cf69d4045e3ea67db300a95370dec5aefe`).

## Delayed-input and layout-specific regressions

The baseline and candidate delayed-input profiles each completed 330 ticks with 10 actual corrections, 65 replayed frames, and 15 waits. Both ended at frontier and confirmation 330. The full cross-source canonical state difference was empty. The layout smoke passed shared-reference preservation, distinct-but-equal Array and Dictionary identity, typed empty and nonempty Dictionaries, odd-entry rejection before live-state restoration, and decoding of an explicit self-reference record.

Timing is observational only. The candidate recorded 50.71 ms mean step and 20.46 ms encode per save; the frozen PBA baseline recorded 69.44 ms and 30.46 ms/save. A restored-baseline sample was 44.69 ms mean step. This spread shows substantial run/load variation, so these samples do not establish causal or stable timing improvement. No 30 Hz claim follows from them.

The explicit self-reference regression covers decoding a prebuilt reference graph. A separate synthetic self-cyclic Dictionary encoder probe reports `Max recursion reached` in both frozen baseline and candidate because the existing encoder hashes a container before resolving its identity. This pre-existing encoder boundary is not changed by the layout work; this report does not claim synthetic cyclic-container encoder support. The flat-specific smoke has the known macOS certificate lookup error (`get_system_ca_certificates`) in its log, but no script/assertion error and the success marker is present. Its log is `/private/tmp/bvn26-perf-opt-r3/flat-dictionary-smoke.log` (SHA-256 `c168b76651ca9e3d7043e387a6b5858816cf2e97a99d6a809866d1f887d6c868`).

## Native online-pair check and limits

I independently ran `online_match_pair_smoke.gd` against the flat candidate. It exited 0, passed the frame-15 bootstrap late-input correction and JSON roundtrip, reached frame 331 with equal checkpoint hashes and six P1 rollbacks, then passed pause/resume barriers, recovery convergence, timeout abort, result commit, and new-epoch rejection. The captured log is `/private/tmp/bvn26-perf-opt-r3/acceptance-online-match-pair-flat.log` (SHA-256 `c383d1e1b0acdd90b4fa7d3b9bceccd38d67aaee66c1ba2aab0499a633d532c8`).

This test uses in-process fake transport; it does not exercise WebRTC, two browser peers, rendered cadence, or the user's real match. Godot logged the same macOS certificate lookup error. The process also reported 7 ObjectDB instances and 3 resources still in use at shutdown; it still exited successfully. Keep that cleanup warning visible for follow-up.

The raw P1/P2 evidence and its identity/timing limits are documented in the R2 report; neither those logs nor this headless pair smoke establish that this build sustains real-time 30 Hz. A paired, same-build Web test with actual delayed corrections remains a separate gate.

## Visible browser candidate burst (not a cadence pass)

I independently checked the completed raw report `/private/tmp/bvn26-perf-opt-r3/web-burst-candidate.json` (SHA-256 `a04cad650ac9bbde4e1e1572d7583d7c40fbf90dabae59df2fc7aa064e710ee3`). Its pair ID is `checkpoint-flat-dict-r3-20260928`, source is `candidate`, status is `complete`, and its source fingerprint `849bc06497ba2ff622151d65ff2121f6dd809c8c0a5b4a28e01409d038dd64d5` matches the generated manifest's build fingerprint. The checkpoint, simulation-state, manifest, and `main.gd` SHA-256 fields match the candidate files. The runtime marker is `battle-local-pba-dict-flat-v2`. The earlier export with the stale R2 identity is excluded.

The report records one visible Chrome 153 run at DPR 2 with Godot 4.7.2. It warmed for 90 frames, then measured 330 frames from `user-log-r01`: 222 recorded input ticks (28–249), neutral padding at 1–27 and 250–330, and no harness-added attacks, assists, or supers. In `rollback_no_late_input`, it completed 331 saves with zero rollbacks and zero replayed frames. `receive_plus_step` mean was 18.814 ms (p95 23.900, p99 25.300, max 26.900); encode/pack/retain totals were 2.7763/0.5640/0.0740 seconds, about 8.39/1.70/0.22 ms per save. The report explicitly sets `cadenceMeasured` false. This is a candidate-only burst, with no same-session baseline, no late correction, and no second WebRTC peer; its timing is an observation, not a speedup or 30 Hz result. The JSON remains under `/private/tmp` and is not copied into the repository.

## Reproduction

Run from the repository root:

```sh
/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot --headless --path godot --script res://tests/battle_checkpoint_flat_dictionary_smoke.gd --log-file /private/tmp/bvn26-perf-opt-r3/flat-dictionary-smoke.log

/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot --headless --path godot --script res://tests/battle_checkpoint_flat_graph_compare.gd --log-file /private/tmp/bvn26-perf-opt-r3/acceptance-flat-graph-compare.log -- /private/tmp/bvn26-perf-opt-r2/candidate-graphs.txt

/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot --headless --path godot --script res://tests/online_match_pair_smoke.gd --log-file /private/tmp/bvn26-perf-opt-r3/acceptance-online-match-pair-flat.log
```

The comparator source, test scripts, and all raw logs remain in the working tree or `/private/tmp`; no private source log was copied into the repository.
