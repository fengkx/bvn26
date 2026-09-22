# Lee natural frame 1288 callback

This evidence pairs the actual source run
`lee-callback-round-loss-failure-r06` with its matching native fixture. Source
build, raw event tape, fixture and instrumentation hashes are frozen in
`preflight.json`; the fixture preserves the two-round KO/reset, real Timer,
normal inputs, and 2400-fight-tick horizon. The native probe ran at the measured
30 Hz execution profile and awaited a monotonic wall-clock deadline for every
logical fight tick. It did not set the timer result or jump to a source frame.

Reproduce the accepted callback projection after `prepare.py` verifies the
source inputs and hashes:

```sh
python3 evidence/characters/lee/godot/callback-exact-r18/prepare.py
"$GODOT" --headless --path godot \
  --script tests/lee_callback_exact_probe.gd -- \
  "$PWD/evidence/characters/lee/godot/callback-exact-r18/fixtures/round-loss-failure-1288-r06.json" \
  "$PWD/evidence/characters/lee/godot/callback-exact-r18/out-run-r03/round-loss-failure-1288-r06.json" \
  > evidence/characters/lee/godot/callback-exact-r18/engine-r03.log 2>&1
python3 evidence/characters/lee/godot/callback-exact-r18/compare_1288.py
```

`comparison-r01.json` records the source/native pair. Both sides observed P1
frame 1288 enter and exit with `action=0` and decoded `ql=300`; the setup,
fighters, helpers, stage and input tape match. This is a four-field callback
match only. The source marker is at fight tick 2263 / 101119 ms; native reaches
it at fixture tick 2228 / physics tick 2504. The real-clock replay logs its
measured deadline drift and MatchCountdown timeout callbacks. The 35-tick
phase difference is still under investigation and is not treated as full
timer, round lifecycle, state, or character parity.

R02 is preserved as a failed/superseded probe attempt because it accessed a
nonexistent pause property and ran beyond terminal state. R03 is the corrected
run: it observes the natural callback and stops at the real terminal transition.
