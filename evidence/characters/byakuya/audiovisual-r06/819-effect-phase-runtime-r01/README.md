# Byakuya 819 effect placement phase, runtime r01

Scope: source-backed focused parity for the 819 helper presentation callback.
This is not a complete visual or character parity claim.

Source evidence: `../819-effect-phase-source-r04/source/target-events.txt` and its raw SHA.
At Flash root observation `p1=819`, helper frame 2 is present while `xgmc0` is undefined. At the next root observation `p1=820`, helper frame 3 and effect frame 2 are present.

## SOURCE_FIRST

1. `scripts/fighter/fz/kon.json`, frame 2 `DoAction.as` calls `_root.fzccXg(this)`.
2. `scripts/main.json` resolves that call through `addChildXG`, which places `XG_fzcc` under `root.game.layer_effect`; the child starts its own timeline at frame 1.
3. The helper's frame 2 is observed before the placement is visible to the same root observer. The new child is first observed on the following callback; no observer-only removal or manual frame offset is used.
4. The source invariant is helper frame 2 at actor 819 with no effect, followed by helper frame 3 and effect frame 2 at actor 820. A newly placed child has an independent callback clock.
5. The invariant is evidenced by raw source events at sequences 3965--3973 and 3993--4001, and reproduced with the same helper/helper fixture by the Godot probe below.

Godot command:

```sh
/private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot -s res://tests/byakuya_819_runtime_probe.gd -- /tmp/byakuya-819-runtime-fixed2
```

The probe has fail-closed assertions for the two root-observer boundaries. The production helper activation now queues its initial frame script through `source_child_frames`; standalone probes without that connection retain direct behavior. No observer-only hide/delete or effect-specific frame offset is used.

Regression commands passed with this runtime: `combat_smoke.gd`,
`helper_duration_reference.gd`, `helper_pause_semantics.gd`,
`helper_presentation_smoke.gd`, `ai_helper_state_smoke.gd`, and
`kon_helper_smoke.gd`. `helper_repeat_contact_smoke.gd` reproduces its
pre-existing touching-edge assertion failure even against the repository
baseline; it is not counted as evidence for this phase change.
