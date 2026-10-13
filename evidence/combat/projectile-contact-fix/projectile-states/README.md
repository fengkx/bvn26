# Original-player projectile state references

Flash Player Debugger 32.0.0.465, Godot 4.7.2, macOS 26.7. Source SWFs and
bundles remain unchanged. `build.json` records input and instrumented-copy hashes;
compressed events/diffs and input, random and clock records retain provenance.
The observer reads the authored depth after root `aiState(p2)`, follows renames,
and excludes earlier decoration clips without a `played` local. It writes no
battle fields. Native observation reads authored matrix twips before Vector2
conversion; comparison has no tolerance or rounding.

| Case | Child states | Post-contact states | Fighter states |
|---|---:|---:|---:|
| Naruto neutral ranged | 22/22 | 18 | 602/602 |
| Hitsugaya guarded air ranged | 27/27 | 18 | 602/602 |

All fields match exactly: child frame, local X/Y, played, movspeed, plus the
existing 14 fighter fields. Fixtures preserve the archived inputs/setup and add
only `projectile_probe`. Neutral/air-target Hitsugaya damage alone does not take
the child callback contact branch; the archived guard fixture does.

`before.projectiles.json` is an actual replay with the affected combat/controller
files restored to bf988e6e; all files were restored afterward. The comparator
rejects 22/22 Naruto and 27/27 Hitsugaya rows because played is undeclared;
movspeed differs in 18 post-contact rows per case. **Position and child playback
already match in these two old-data cases**: legacy runtime compatibility masks
the missing source-local writes. This is not evidence of observed flight drift.
`before-comparison.json` records separate per-field counts. The Python regression
also mutates each saved child's post-contact X, frame and movspeed independently
and requires all six mutations to fail, so continued flight or wrong playback
cannot silently pass the new exact comparison.

Reproduce both live Godot replays against retained original-player events:

```sh
python3 tools/test_projectile_contact_references.py --projectile-states --godot /path/to/Godot --output /tmp/bvn-projectile-states
```

Expected: `cases=2 matched=2 states=1204 projectile_states=49`. The runner verifies
source and fixture hashes and requires successful Godot execution without SCRIPT
ERROR, full row counts, exact values and at least two source post-contact rows.
The two captures validate this contact branch, not every move or audiovisual/Web
parity. See the parent [source gate](../source-first.md) and [review results](../review.json).

To recapture in separate temporary directories, use the existing builder and
native player capture tools (the standalone player may activate its own window):

```sh
python3 tools/probes/build_ai_reference.py --ffdec /path/to/ffdec-cli.jar --output /tmp/minren-projectile-build --run-id minren-projectile --frames 300 --p1-character 鸣人 --move-case evidence/combat/projectile-contact-fix/projectile-states/minren-case.json
python3 tools/probes/capture_native_player.py /tmp/minren-projectile-build /tmp/minren-projectile.log --allow-window-activation
python3 tools/probes/collect_ai_reference.py --build /tmp/minren-projectile-build --capture /tmp/minren-projectile.log --output /tmp/minren-projectile-source
```

Use the Hitsugaya fixture and `--p1-character 日番谷` with distinct output paths
for the guard case. Do not overwrite retained expectations to make a replay pass.
