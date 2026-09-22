# Byakuya controller decision probe

Command:

```sh
/private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot -s res://tests/byakuya_ai_decision_probe.gd
```

This is a bounded source controller callback probe, not a full match replay. It restores the complete declared predicate read set and the source-observed geometry/random-local values for two clean-run decisions:

- fight tick 12: source `nornalhit=true`, then the next Byakuya state is frame 169 (`砍1`).
- fight tick 149: source `defence=true`, then the next Byakuya state is frame 849 (`防御`).

Godot dispatch runs the generated `DefineSprite_631/frame_1/DoAction.as` controller hook at the correct callback phase. Results are `2/2` predicate matches and `2/2` goto matches: attack reaches `砍1`/frame 169 and defence reaches `防御`/frame 849. The source sequence ids and next-state evidence are recorded in `result.json`.

The read set is explicit in `result.json`; per-decision minimal sets are also recorded. Source owner is `DefineSprite_631/frame_1/DoAction.as` from `scripts/fighter/Byakuya.json` / `game/fighter/Byakuya.swf`.

Scope remains one callback decision per fixture. It does not certify boot, intro, helper lifecycle, or full 180-tick AI parity.
