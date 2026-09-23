# Native battle rollback evidence

Date: 2026-09-22. Engine: Godot 4.7.2.stable.official.ed1daf0bf.

`results.json` retains runner markers, the tested scope and reviewed source hashes.
Run with:

```sh
python3 tools/test_rollback_foundations.py --godot /path/to/Godot --report /tmp/rollback-results.json
python3 tools/test_shared_modes.py --godot /path/to/Godot
```

The real battle fault case compares a 330-frame reference with delayed,
reverse-order, duplicated remote inputs and a temporary delivery outage. A second
freshly initialized battle must also produce the same complete checkpoint. Fixed
input delay is tested separately, including immutable sampling and a zero prediction
window. The roster case tests eight checkpoints per pairing over all 11 enabled
fighters, four helpers and ten maps. Round cases cover KO, nextfight, subsequent
round state and the final confirmation barrier. The checkpoint case includes a
real recorded BODY callback, negative facing scale and frozen-shadow revival.

External timer/intro schedules are synthetic fixture inputs, not new Flash cadence
measurements. Coverage is representative, not every move/mirror/interaction. The
state format requires its battle-local retained-node/resource cache; it is not an
importable savegame. Native profiling counters are diagnostic totals, not Chrome
p95/p99 acceptance. The renderer still builds intermediate replay frames.

The runner rejects script errors, missing markers and native errors. It records
headless audio-shutdown warnings only when every leaked instance is an audio
stream/playback object identified in verbose output; those engine shutdown records
are separate from battle-state correctness. The macOS certificate lookup warning
is likewise classified explicitly.

Source parity remains scoped to the unchanged shared PvP/training-timer references:
602 actor states each. No original migration milestone, browser result or real
internet match is certified by this evidence.
