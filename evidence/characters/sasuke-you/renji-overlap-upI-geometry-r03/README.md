# You callback geometry probe r03

This is an isolated original Flash Debugger probe for the fixed upI overlap. It
does not modify `game/`, `scripts/`, or runtime code. The raw log and events are
compressed to avoid duplicating the formal uncompressed capture.

## Source-first five questions

1. **Per-frame script:** You `atm1` runs the source clip action at
   `scripts/fighter/fz/you.json`, `frame_48/PlaceObject2_24_3/...enterFrame`;
   the callback calls `this.hitTest(_root.game["p" + _parent.pn].mc.bdmn)`.
2. **PlaceObject/MOVE:** `atm1` is placed at You local frame 48, depth 3;
   its source matrix is scale `(1.7922058,0.5614166)`, translation `(538,-345)`.
3. **Leaving the label:** a hit calls `_parent.gotoAndPlay("攻击2")`; no hit
   follows the authored timeline fallthrough.
4. **Source invariant:** the callback reads the current `bdmn` instance at the
   moment it runs; no synthetic hit is allowed when bounds are unavailable.
5. **Same-input comparison:** r03 uses the formal upI fixture and its 602
   fight-tick state rows per actor match canonical source values exactly.

## Callback-before-observer evidence

The probe records P2 `mc._currentframe` separately from `bdmn._currentframe`.
The root observer snapshot is one frame behind the callback's observed `mc`
frame because the callback runs before the observer serializes state for that
display tick:

| fight tick | display tick | P2 `mc._currentframe` in callback | `bdmn._currentframe` | target bounds | hit |
|---:|---:|---:|---:|---|---|
| 62 | 514 | 969 | undefined | all undefined | false |
| 63 | 515 | 970 | undefined | all undefined | false |
| 64 | 516 | 971 | undefined | all undefined | false |
| 65 | 517 | 972 | 1 | `(334.4,274.1)-(368.95,354.35)` | true |

The corresponding canonical observer rows report P2 root frames `626, 969,
970, 971, 972` at fight ticks 62 through 66. The probe does not infer whether
an undefined member means a missing reference; the measured fact is that target
bounds fields are unavailable and hitTest is false at ticks 62–64.

## Verification

`compare.json` reports canonical/probe `state=602/602` and
`helper_state=602/602`, both `same_by_fight_tick=true`; startup rows are
reported separately. `events.jsonl.gz` contains four `you_geometry` events at
fight ticks 62–65, captured before the original hitTest call.
