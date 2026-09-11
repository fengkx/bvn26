# You/Renji overlap dispatch probe r01

> **Historical superseded:** this diagnostic is retained as the earlier red/pending record. The repaired upI/upU acceptance is in [renji-overlap-upI-upU-fix-r01](renji-overlap-upI-upU-fix-r01/README.md).


This is a focused source/native diagnostic for the explicit base-form fixture
`/private/tmp/sasuke-you-renji-down-ranged-overlap-start20-r01.json`. The
fixture uses P1 Sasuke at `x=300`, P2 Renji (恋次) at `x=350`,
`p1_helper=鼬` (`you`), `p2_helper=魂` (`kon`), energy `300` on both sides,
and summon input on P1 at ticks 10..13. P2 holds `down+ranged` at ticks
20..23. The source capture is
`/private/tmp/sasuke-you-renji-down-ranged-overlap-start20-original-r02/collected/events.jsonl`.

The exact production replay command was:

```sh
/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot \
  --log-file /private/tmp/sasuke-you-renji-down-ranged-overlap-start20-r01-native-r01/engine.log \
  -s res://tests/move_case_reference.gd --quit-after 1400 -- \
  /private/tmp/sasuke-you-renji-down-ranged-overlap-start20-r01.json \
  /private/tmp/sasuke-you-renji-down-ranged-overlap-start20-r01-native-r01/native.json
```

The source/native fighter comparator and helper comparator both report
`matched`, with 602/602 rows and zero differences:

```sh
python3 tools/probes/compare_mode_reference.py \
  /private/tmp/sasuke-you-renji-down-ranged-overlap-start20-original-r02/collected/events.jsonl \
  /private/tmp/sasuke-you-renji-down-ranged-overlap-start20-r01-native-r01/native.json \
  --output /private/tmp/sasuke-you-renji-down-ranged-overlap-start20-original-r02/compare-native-fighter-r01.json
python3 tools/probes/compare_helper_reference.py \
  /private/tmp/sasuke-you-renji-down-ranged-overlap-start20-original-r02/collected/events.jsonl \
  /private/tmp/sasuke-you-renji-down-ranged-overlap-start20-r01-native-r01/native.json.helpers.json \
  --output /private/tmp/sasuke-you-renji-down-ranged-overlap-start20-original-r02/compare-native-helper-r01.json
```

The source dispatch is visible at P2 frame 383/action 2 on tick 24 and the
`zh2atm` active frame 394 on tick 35. Sasuke is hit at tick 36 (HP 1000 to
960). You is at frame 48 with source `atm1` on tick 62 and reaches frame 92
on tick 63. P2 is paused on ticks 38..95, so the receiver's source
`gameRunning()` gate is false during the retained helper attack. After the
pause, P2 resumes at frame 397/398, reaches frame 969 (`被打`) on tick 99,
and the first You `atm2` damage is applied on tick 100: P2 frame 970, HP
1000 to 960, hits 0 to 1. Further You damage occurs at ticks 116, 132, and
148; the final `atm3` row is frame 983, HP 780, hits 4. The source and native
rows are identical at each of these boundaries.

The production call chain is `godot/ai_combat_services.gd`:
`invoke("receive")` -> `CombatResolver.resolve_incoming`, called from the
fighter BODY receiver callback. `CombatResolver.resolve_helpers` is an
independent polling/test entry and is not used as production evidence here.

The corresponding `up+special` start-20 native control reaches P2 frames
586/592/624 and You frames 48/92/128 at ticks 107/108/144, but P2 remains
paused through tick 140; its first You damage is tick 145 after resume. The
start-40 input is swallowed by pause (P2 has no 586/592/624 dispatch), so it
is not an overlap case. No shared runtime change is justified by this probe;
the up+special same-input original capture remains pending.

## Hashes

| artifact | SHA-256 |
| --- | --- |
| fixture | `753496e886291d805a1c06abc5588879c8a32513f0dbfab0cdfb1c015689d7de` |
| source events | `f2a7471ed82d0e81474c721da1c51f8584a352baeb15eb7b9e2092673845fb31` |
| native fighter | `26d9d572355328cea31cd2f0c5709c19a90f7fc27a969ae437b7cbb84b2c0b5e` |
| native helper | `a4c5e116ec98361e9a2f5babfead9de5ac43c23798beba540520c9bceee1db52` |
| fighter compare | `04ecd4141e07f2e4dba08c9888cd472b3d86689d8709b5d6de5760da0a27d3dc` |
| helper compare | `cddd61fcefa0567449e90860f9ac11c0a549f829bf72040ef61f809ef11977f7` |
| `godot/ai_combat_services.gd` | `de60321a9a529c288e002a303430933e96405c77059533af9e0d5bdd0b57d7e4` |
| `godot/combat_resolver.gd` | `1629558d0e1c0fd2350620784aac8fb328ce82b592ace3af9f498b432acb1332` |
| `godot/fighter_runtime.gd` | `cbb079e264c2777610a2dfb33728906c75e72c20ad6751f2da2669677e78c07d` |
| `godot/helper_runtime.gd` | `5a60b5ae940159ddea9e3067c20ab483f15d2acc7320a14eb2b2a95538cae860` |
| `godot/generated/fighters/renji/combat.json` | `88a08e1925c0b4f22dc827c68f8152de36ff0dac2502409c607986fbfb48ebfc` |
| `godot/generated/helpers/you/combat.json` | `4db767abd6c563eb630960c5e5bbef8841ddaa4426ccab58345172ee9fba4c49` |

