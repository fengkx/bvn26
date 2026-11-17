# Guard and guard-break rendered observations

Ten same-input native Flash/Godot captures cover five selected forms, guarding
and receiving a guard break. All ten compare 66 actor states without differences.
These bitmap probes did not enable root-position events; the raw root comparison
therefore reports zero source rows, not a position mismatch. The separate 97-case
matrix does include and match root-position events.

The contact sheets retain the source at left and native render at right at tick
32. Guard silhouettes match (Naruto cloak shield, Hitsugaya ice shield, Rukia,
Sasuke wing guard and Ichigo sword guard). Guard-break actor states and health
settlement match. These are visual inspections, not exact-pixel passes.

Observed presentation differences to investigate in the broader audit:

- Ichigo's attacking sword and some ice/hit particles differ in visual phase.
- The native upper HUD is absent in four guard-break snapshots while present in
  Flash; check the terminal-observer capture boundary and HUD refresh before
  changing gameplay rendering.
- Flash's wall-clock countdown advances during expensive bitmap serialization;
  the fixed-frame native snapshots do not share that elapsed-time input.

Each case retains its fixture, original instrumentation, raw-log digest, complete
bitmap samples at ticks 12 and 32, all non-bitmap events, native actor traces and
comparison. Full raw capture files remain in `/private/tmp/bvn-forms-live`.
