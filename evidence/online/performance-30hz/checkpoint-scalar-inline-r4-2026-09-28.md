# Checkpoint scalar dispatch bypass (2026-09-28)

## Scope and change

The user supplied a real network-match log, `P1 over network.json`. The build,
commit and PCK identity fields are empty, so the local source cannot be assumed
to match the running game. The reported match averaged 14.86 Hz over 167.41 s
and 12.09 Hz in the final 45.49 s. Across the log, 344 corrections replayed
1,365 frames; ordinary `simulation_step` averaged 36.75 ms, and each saved
checkpoint averaged 18.72 ms encode, 5.55 ms pack and 0.516 ms retention.
Correction receive time overlaps `input_receive` time, so those totals must not
be added. This evidence motivated a local checkpoint-encode candidate; it does
not identify the source version running in that match.

The candidate bypasses `_encode()` dispatch at the array-entry, dictionary
key/value and ordinary object-field call sites for exactly the builtins already
returned directly by `_encode`: nil, bool, int, String and finite float. The
shared `DIRECT_SCALAR_BUILTINS` list keeps that set aligned. `StringName` and
non-finite floats still use the existing value codec. Other values continue
through `_encode()` unchanged. Container identity, aliasing, field/entry order,
snapshot contents, rollback policy, timers, random state and source combat
rules are unchanged.

The candidate is layered on the accepted flat-PBA checkpoint format. The
frozen pre-candidate `battle_checkpoint.gd` SHA-256 is
`16ebed2dc1fa5fc45f11c61053261db02255ce2474017de76ac0bea7e54f78fc`; current
candidate SHA-256 is
`a95ed7636da80b918e8695d600d6fcb6c590de58a9d68fa0a2f3db41b515f201`.
`simulation_state.gd` remains
`847277c7bfd89b58f107b56ad8375b9c774dd2b5e0b3dcd8d29641ffadf683cb`, and the
graph marker remains `battle-local-pba-dict-flat-v2`.

## Structural and correctness evidence

The frozen 15-save profile at
`/private/tmp/bvn26-online-encode-r4/profile-short.log` counted an average
1,765.6 eligible scalar values per save that previously entered `_encode()`;
the same sample's average recursive `_encode()` call count was 3,405.2 per
save. The direct values therefore account for about 52% of calls in that
representative sample. This is a call-count estimate, not a time reduction.
A separate 16-frame candidate capture reported 1,639.6 `_encode()` calls per
save and byte-identical graphs against the frozen 16-frame baseline. Those
samples are not a paired timing experiment.

For the longer check, the frozen 331-row tape is
`/private/tmp/bvn26-perf-opt-r2/candidate-graphs.txt`, SHA-256
`8f9424453b59a449897297da7c772c2fdf8e08110cee82131c54c70649f266ae`. The tape
contains the earlier pair-array dictionary representation. The comparator
derives the current flat representation by changing only each old
`dictionary.entries` array from pairs to the same ordered flat sequence, then
compares `var_to_bytes` output with the candidate PackedByteArray at each
frame. It does not sort, normalize, omit or rewrite any other field. All 331
derived graphs were byte-identical to the candidate. This is a derived-format
reference from the frozen older tape, not a direct capture from the R3 source.
The pair-array and graph-byte savings shown by the comparator belong to the
already accepted flat-dictionary format change; they are not savings from this
scalar-dispatch candidate.

The 330-tick delayed-input profile completed with frontier and confirmation
330, 10 corrections, 65 replayed frames and 15 waits. Its complete canonical
state comparison returned an empty `State.first_difference`. The reference
`/private/tmp/bvn26-perf-opt-r2/baseline-canonical-state.bin` has SHA-256
`c5ae5a388f63db1d0a85a52673e3324c310e1a040691ce07cc6310e9967a842a`; its
`baseline-canonical-check.log` was produced from the old `battle-local-v1`
String/hex baseline whose frozen `battle_checkpoint.gd` and
`simulation_state.gd` copies hash to `fa7d03d2719b2ca61738aaa30f7e5d0b17da583342ef3a3e4e878ce7b9fbcbac`
and `dfc0b2c83eaf33418b7516746ee6934df1ef8a3d89e89c566ba4417a86b6bbc4`.
This is a cross-version logical-state comparison. It is not an R3-to-R4 raw
state-byte comparison. A separately captured candidate canonical-state file
is `/private/tmp/bvn26-online-encode-r4/candidate-canonical-state.bin`, SHA-256
`870ad5202175749e4fbcd10b433b2ddff843b5261f30048fe1df2c97f8b47647`; its
file hash is recorded for provenance, not used as the equality assertion.

The focused regressions passed:

- `battle_checkpoint_scalar_inline_smoke.gd`: nil, bool, int, finite float and
  String stay direct; `StringName`, infinity and NaN keep the wrapped codec and
  round-trip with their types intact.
- `battle_checkpoint_immutable_cache_smoke.gd`: two consecutive saves, with a
  warm immutable-field cache, have identical full snapshots and graph bytes.
- `battle_checkpoint_smoke.gd`: rejection of wrong frame/build/version,
  corrupted bytes/length/type, foreign and expired snapshots; copy-on-write and
  retained-graph checks pass.
- `battle_checkpoint_flat_dictionary_smoke.gd`: alias identity, distinct but
  equal containers, typed empty/nonempty dictionaries, explicit reference
  decoding, and odd-entry rejection before live state changes pass.

Godot 4.7.2 emitted the existing macOS certificate lookup warning
`get_system_ca_certificates`; each listed run exited 0 with its success marker
and no GDScript error. Timings from this host are excluded from attribution.
No new two-peer WebRTC run was made, and no post-change real-match frame-rate
gain is established. The source version of the supplied P1 log is unknown.

## Reproduction

Run from the repository root. Godot is
`/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot` (4.7.2 stable).
All command logs and tapes remain in `/private/tmp`.

```sh
/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot --headless --path "$PWD/godot" --log-file /private/tmp/bvn26-online-encode-r4/graph-331-derived-raw-candidate.log --script res://tests/battle_checkpoint_flat_graph_compare.gd -- /private/tmp/bvn26-perf-opt-r2/candidate-graphs.txt

/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot --headless --path "$PWD/godot" --log-file /private/tmp/bvn26-online-encode-r4/delayed-state-scalar-candidate.log --script res://tests/rollback_delayed_input_profile.gd -- compare-state /private/tmp/bvn26-perf-opt-r2/baseline-canonical-state.bin

/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot --headless --path "$PWD/godot" --log-file /private/tmp/bvn26-online-encode-r4/delayed-state-candidate-artifact.log --script res://tests/rollback_delayed_input_profile.gd -- write-state /private/tmp/bvn26-online-encode-r4/candidate-canonical-state.bin

/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot --headless --path "$PWD/godot" --log-file /private/tmp/bvn26-online-encode-r4/scalar-inline-smoke.log --script res://tests/battle_checkpoint_scalar_inline_smoke.gd

/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot --headless --path "$PWD/godot" --log-file /private/tmp/bvn26-online-encode-r4/immutable-cache-warm-smoke.log --script res://tests/battle_checkpoint_immutable_cache_smoke.gd

/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot --headless --path "$PWD/godot" --log-file /private/tmp/bvn26-online-encode-r4/checkpoint-boundary-smoke.log --script res://tests/battle_checkpoint_smoke.gd

/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot --headless --path "$PWD/godot" --log-file /private/tmp/bvn26-online-encode-r4/flat-dictionary-boundary-smoke.log --script res://tests/battle_checkpoint_flat_dictionary_smoke.gd
```

The online compatibility manifest was regenerated with
`python3 tools/build_online_manifest.py`. Its build fingerprint is
`334f76d11457501fc204699cb793a3ec1511e8097d37c24f140931fb57f9c0c1` and its
content fingerprint remains
`a52c9b9391f280f06bb5b205607fccdf23f9fe3afade41fbaecc003d5bb063e7`.

The repository-level performance task M4-03 remains pending: this scoped native
correctness work neither measures stable low-load timing nor accepts a real
two-peer 30 Hz match.
