# Byakuya AI r02

This run verifies the production Vs-Com slot wiring with Byakuya as the CPU
fighter under test:

- P1: 一护, human
- P2: 白哉, CPU (`p2_cpu=true`)
- helpers: 魂 / 魂
- mode: 2, AI level 5, stage 现世

The native Flash run is retained in `native-build.json`, `native-random-tape.json`,
and `native-clock-tape.json`. It completed 4,813 events with 206 random records;
the native clock tape is empty for this capture. The Godot replay uses a fixed
runtime tape generated from the same configured production path and consumed five
Byakuya random draws with no script error or random-site failure.

This is wiring and deterministic-random evidence. It is not a claim of AI
behavior parity: the 180-tick replay stayed in the standing action and a valid
native clock/event-mapped behavior comparison is still required.

The follow-up full replay uses `native-byakuya-random-tape.json`: the one main-scene
record is excluded and the 205 Byakuya records are re-indexed as 41 refreshes × 5.
`godot-full-random-replay.json` consumes all 205 records over 180 fight ticks with
an empty failure field. Both native and Godot sampled action 0 (standing); frame
level parity remains pending because the native clock tape has no records and the
native/Godot frame numbering is not yet aligned by a source clock trace.
