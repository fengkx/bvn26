# Recovery movement and cross-actor callback order

Status: source-derived recovery callback implemented; cross-actor scheduling remains
unresolved. Neither the controlled probes nor the partial replay establish match parity.

## Source and implementation

`scripts/fighter/minren.json`, preserved path
`DefineSprite_764/frame_1064/PlaceObject2_16_28/CLIPACTIONRECORD onClipEvent(enterFrame).as`,
adds or subtracts `Math.round(_parent.speed / 2)` while `_root.zhanting == false`.
The controller's parent is the BODY and its grandparent is the fighter container.
The source callback hash is
`4b5b0b8cd00a1a07a11bc12b23d5897342e71260c34faee7ee1bf40ff81b5043`.
The source timeline places the controller at 1064, retains it through 1067 and removes
it at 1068. New placements do not receive an enterFrame on their birth tick: ordinary
playback moves on 1065, 1066 and 1067, for a total of 12 pixels at speed 8.
Frame 1069 explicitly goes to standing and plays; it is not an inferred action exit.

`compile_ai_body.py` recognizes the complete guarded movement source template and
compiles its expression with an explicit scope binding. `source_body_callbacks.gd`
dispatches the generated method through the existing instance lifetime tracker.
The player hurt-lifetime smoke covers birth, removal, pause, reverse facing and source
rounding. Identical templates at 172 and 190 are compiled too, but player non-hurt
dispatch is still legacy and is not claimed migrated by this change.

`boundary-recovery-r08.json` replays the unchanged `body-clock-r08` input/random/clock
capture. Across 375 snapshots per fighter, P1 relative displacement error is now zero;
P2 still has a 6-pixel error. Initial native float offsets are retained separately.
The first 460 source BODY boundaries match; event 461 still differs. Random and clock
failure fields are empty. The recovery fix does not resolve the cross-actor mismatch.

## Controlled original-game probes

Build with `tools/probes/build_ai_reference.py`, `--frames 10 --body-boundaries
--recovery-order-probe`; add `--recovery-walk-first` for the second variant.
The fixture runs after Ready, cancels the AI interval and supplies explicit samples.
P1 starts at X=330, source frame 1064; P2 at X=351, frame 10; goran=60 and the other
four samples=400. These are controlled fixtures, not natural match golden traces.
Full source/build hashes, instrumentation diffs and events are retained in
`recovery-order-r09/` and `recovery-order-r10/`.

| Fixture goto order | First callback order | P2 X after the recovery callback |
|---|---|---:|
| P1 1064, then P2 10 | moveLeft, recovery enter, recovery exit | 345 |
| P2 10, then P1 1064 | recovery enter, recovery exit, moveLeft | 351 |

Both captures report identical container depths: P1=-16375, P2=-16377. In the second
case recovery first moves P1 to 334, so P2's source `351 > 334 + 20` is false. In the
first case `351 > 330 + 20` is true and the source subtracts speed 6.
Both run exactly three recovery callbacks. Recheck the retained ordered events with:

```bash
python3 tools/probes/check_recovery_order.py
```

The old two-sibling depth probe remains evidence for that fixture only. It does not
justify running complete fighter subtrees in a fixed order. The pair above proves
that cross-actor order can change with goto order at unchanged depths. It does not
alone prove a general reverse-creation registry: goto may rebuild or reorder retained
instances, and the BODY callback's relation to each child still needs explicit checks.
The fixture's historical `created first` label describes its intended construction;
the actual proven operation is the recorded goto order.

Next: establish registration/reconstruction and retained-instance behavior, then share
callback scheduling across actors and rerun the unchanged r08 replay. Do not swap the
whole actor array or relax the 20-pixel comparison to match this one situation.

Follow-up: the retained/recreated nested-clip probe now supports a shared callback registry. Also, the earlier global key override did not inject input. See [registry and input correction](callback-registry-and-input.md) for the implementation, new reference, and remaining limitations.
