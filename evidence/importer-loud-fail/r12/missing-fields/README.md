# Native target-body missing fields and unordered comparisons

**Do not initialize these fields to zero or translate unordered comparisons using
Python/JavaScript assumptions.** Five native original-SWF probes produced 26
observations plus five completion events. No child definitions, actions,
placements, or non-DoAction root tags changed; each builder verifies their hashes.
Only the root frame-1 observer is replaced. Locked sources remain unchanged.

## Exact source scope

The entire locked `scripts/fighter/Sasuke.json` bundle contains exactly two
`khitn` occurrences, both in body 1019:

- `DefineSprite_1019/frame_128/DoAction.as`: `khit=1; 动作=1; khitn++;`.
- `DefineSprite_1019/frame_135/PlaceObject2_16_36/CLIPACTIONRECORD onClipEvent(enterFrame).as`:
  `if(_parent.khitn < 3)` gates `airhit()` and `gotoAndPlay("跳砍")`.
  The following `airMagichit()` branch is independent.

The entire locked `scripts/fighter/yihu.json` bundle contains exactly one `nn`
occurrence, in body 1180:

- `DefineSprite_1180/frame_143/PlaceObject2_651_32/CLIPACTIONRECORD onClipEvent(enterFrame).as`:
  when unpaused, wrapper Y increases by 10, then `if(_parent.nn >= 1)` gates
  `if(_parent.touch == true)` and `gotoAndPlay("跳招2")`.

Neither field has a declaration/reset elsewhere in its bundle. Each build.json
records the complete occurrence list with exact text/hash, SWF hash, and bundle
hash. This inventory is not a claim that arbitrary external root code cannot
write a dynamic field; it proves why zero initialization is not source-derived.

## Native field observations

`--fighter sasuke` and `--fighter yihu` keep movement paused, enter parent frame 2,
and inspect the real replacement body before/after forcing the target frame.
They trace value, typeof, own-property presence, isNaN, `<3`, and `>=1`.

- Sasuke initially has no own `khitn`; reading it yields `undefined`. Executing
  original frame 128 changes it to an own property with value `NaN`, type `number`.
  A deliberately seeded 0 increments to 1 using the same original action.
- Yihu `nn` remains absent/undefined at frame 143. Seeding 1 and deleting the
  property are explicitly marked diagnostic states, not source behavior.
- For both undefined and NaN, native AVM1 `<3` produces `undefined`, false in a
  branch. Native `>=1` produces **true**. A zero default would change both sites.
- Reissuing gotoAndStop(128) while already stopped on 128 does not rerun the frame
  action in this probe: after deletion the field remains undefined. That record
  is preserved; it is not falsely reported as a second increment.

## Original controller branches verified

The `--controller-branch` mode temporarily replaces the body's `on_enterframe`
method with a no-op to isolate the original child callback. It sets touch=true,
starts wrapper Y at 0, and unpauses after placing the original controller.
The original helper definitions and CLIPACTIONRECORD bytecode remain unchanged.

- **Yihu:** before callback body 143, nn undefined, touch true, Y 0; next observation
  body 151 (`跳招2`), nn undefined, touch true, Y 10. The original missing-nn branch
  actually executes; this is not only a recompiled diagnostic expression.
- **Sasuke:** first execute original 128 to produce NaN, then stop on 135. The root
  observer supplies a controlled opponent with sw=false, selects player mode,
  and makes the key predicate true for J and false for U. With NaN, the original
  callback stays on 135. Explicitly seed khitn 0 and the next callback goes to 127
  (`跳砍`). Thus the callback really runs and its NaN gate suppresses the first
  jump; it is not merely inactive because gameRunning/airhit were false.

These are isolated callback semantics, not full-match or complete replacement
parity. Callback lifecycle, target assets and wrapper integration remain subject
to the separate form-runtime acceptance.

## Original bytecode evidence

`original-pcode/` is exported from the locked original SWFs with JPEXS 26.2.1:

- Sasuke 128: `GetVariable khitn; Increment; SetVariable`.
- Sasuke 135: `GetMember khitn; Push 3; Less2; Not; If skip`.
- Yihu 143: `GetMember nn; Push 1; Less2; Not; Not; If exit`.

The first Not in Yihu implements `>=`; the second inverts the condition for the
branch. Less2's unordered result is undefined; Not makes it true. Replacing this
with a host-language NaN `>=` would incorrectly make the actual source branch
false. `observations.json` preserves all 26 field/callback observations.

## Reproduce

Set `FFDEC`, `FLASH_APP`, and a fresh absolute output directory for each case:

```sh
python3 tools/probes/build_missing_form_fields_probe.py --fighter yihu \
  --controller-branch --ffdec "$FFDEC" --output "$OUTPUT"
python3 tools/probes/capture_native_player.py "$OUTPUT" "$OUTPUT/native.log" \
  --player-app "$FLASH_APP" --allow-window-activation --timeout 40
```

Repeat for sasuke, and omit `--controller-branch` for both field-state captures.
The player is the same Debugger 32.0.0.465/Rosetta; each directory records native
capture metadata, original source/build hashes, observer source, and raw trace.
For original P-code export use `java -Duser.home="$SCRATCH" -jar "$FFDEC"
-format script:pcode -export script "$PCODE_OUTPUT" game/fighter/yihu.swf`
(and Sasuke.swf). The original paths are preserved beneath original-pcode/.


## Candidate compiler and Godot regression

The `form_replacement=True` compiler path now discovers bounded undeclared scalar
reads in child numeric comparisons and gives them undefined slots. It does not
invent zero initializers. Unrecognized object/call forms still fail. Default
shipped compiler output is unchanged; this feature is enabled only for candidate
replacement programs. Slots represent scalar reads, not full MovieClip property
presence or reflection semantics.

Candidate controller comparisons use `source_less2`: unordered inputs return
null/undefined; >= and <= apply Not to the appropriate ordered comparison.
`godot/tests/fixtures/missing_form_fields.gd` is generated from the two original
callback sources with exact source hashes. The controlled helper inputs match
the native isolation probe. `AiSourceState` supplies the original increment.

`missing_form_fields_reference.gd` passes **2 sources / 4 branch cases**: Sasuke
NaN suppresses the jump, seeded 0 permits it; Yihu undefined permits the jump,
seeded 0 suppresses it. The additional native `yihu-branch-zero/` capture confirms
the zero control: body 143 remains 143 while Y still advances by 10. This extends
the original four captures without replacing their observations.

Python targeted regressions pass **17/17** (6 new scalar/compiler tests and 11
existing Uryu tests), including exact fixture regeneration, null declarations,
source increment ownership, invalid scope rejection, and comparison lowering.
Both real target contexts and all four CPU/player controllers compile under the
candidate mode; see target-compile.json. Full isolated profiles and recursive
third-form blockers are documented in ../target-profiles/README.md. These results
do not enable a production replacement route.

```sh
python3 tools/probes/build_missing_form_fields_fixture.py \
  --output godot/tests/fixtures/missing_form_fields.gd
python3 -m unittest tools.tests.test_form_undefined_scalars tools.tests.test_uryu_compilers
"$GODOT" --headless --path godot --log-file "$OUTPUT/godot-engine.log" \
  --script res://tests/missing_form_fields_reference.gd
```
