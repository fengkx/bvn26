# Parent replacement source requirements, r07 (2026-10-23)

**The requested four runtime consumers are not completed. Cache acceptance remains
22/26 and build/fingerprint remains FAIL.** This checkpoint adds native evidence,
strict target-load dependency compilation and real target-context compile attempts.
It does not claim 26/26, a completed form port or native/Godot replacement parity.
Production runtime, generated fighter data and renderer are unchanged. No allowlist,
threshold change, new port, merge or deployment.

## What changed

- `parent_form_requirements.py` resolves a literal parent target to an unambiguous
  target body/load, records source hashes, and retains **every** load declaration
  in order, including fields outside the base AI field set and the Key.isDown
  binding. Unknown statements, missing/ambiguous loads and missing body init fail.
  These records are explicitly requirements, not executable runtime events.
- The frame compiler's four hard errors now name the parent frame, replacement
  body/depth and exact load path. The cached requirements catalog carries those
  errors through build validation. No failed context is treated as compiled.
- `build_parent_goto_probe.py` preserves original child definitions, root
  placements and clip actions. Only the root DoAction receives instrumentation.
  It initializes zhanting before the original startup guard (otherwise the movie
  unloads), pauses movement, and forces the original source frame containing
  `_parent.gotoAndStop(2)`. Raw logs, actual programs and hashes are under native/.
- `audit_parent_forms.py` performs real source XML extraction, nested-control
  validation and context compilation for target bodies; temporary exports are
  automatically cleaned. This exposes two additional target-form blockers.

## Native observations — not Godot parity

All four captures have five state observations. Their columns are:
`phase,parent_frame,body_frame,mc===old,sentinel,spd,jumpPower,khit,touch`.

| Source | Original call | Replacement body | Loaded speed/jump |
|---|---|---|---|
| daitu | 458/1309 | 1138 | 17/20 |
| minren | 764/1382 | 1293 | 8/15 |
| Sasuke | 603/1232 | 1019 | 10/15 |
| yihu | 638/1055 | 1180 | 12/15 |

Immediately after the root observer's `mc.gotoAndPlay(source_frame)`, the parent
still reads frame 1 and the body reads that source frame. At the next observation,
the parent reads frame 2 and replacement body frame 2. The injected sentinel is
undefined and khit is reset from 91 to 0. Subsequent body frames are 3 and 4.
`mc === old` remains true despite the field reset. This is observable AVM1 reference
behavior; it does **not** prove that an internal object was reused or that variables
should survive. A Godot node-identity comparison is not a substitute for it.

The observations bound replacement between two phases; they do not measure exact
sub-frame load/frame-script/enterFrame ordering. That ordering, live reference
resolution, callback retirement/re-registration, wrapper state and complete target
assets remain requirements for the missing consumer. The source is expressible;
this checkpoint has not implemented those dependencies.

`root-tag-verification.json` verifies all non-DoAction tags byte-for-byte, including
actual root placement and load records. The builder now enforces this check on
future captures. The initial uninitialized-pause experiment produced no usable
reference and is not used. No original game/ or scripts/ file was modified.

## Target compilation exposes further missing behavior

Actual extracted target timelines produce:

| Target | Result |
|---|---|
| daitu 1138 | Context compiled, 1,407 frames / 66 frames with calls |
| minren 1293 | Hard error at frame 996, line 3 |
| Sasuke 1019 | Hard error at frame 1024, line 3 |
| yihu 1180 | Context compiled, 1,042 frames / 74 frames with calls |

Both errors are the source block `if(_parent.万解 == true) { _root.cbsw(pn); bs = 0; }`.
The parent-scoped condition needs an owner; stripping indentation or emitting the
call/write unconditionally would silently change Flash semantics. These sites are
recorded in target-compile-audit.json and remain errors, not allowlist candidates.
Successful context compilation alone does not supply assets, combat/controller
coverage or the replacement runtime. No target form was added to shipped content.

## Acceptance and remaining blockers

- Frame-call caches **22/26**, build/fingerprint **FAIL** at Yihu 638/1055 with
  target body 1180 and exact load path now included.
- Current placement/control closure checks **89/89**; all **34** source errors
  remain unresolved. This refresh uses the pinned placement catalog and r06's
  62-SWF raw inventory; it is not another raw scan. No placement renderer changed.
- Python **387 run: 385 passed, 2 skipped**, including four new load-requirement
  tests. Native capture **4/4 completed**, 20 observations; **no Godot form parity**.
- GPU **7/7 existing asserted subsets**, Blur **242/242 / 37,280 alphas**, blend
  **38/38** under its unchanged existing contract; Godot smoke **4/4**.
- Strict color comparisons still fail: **3/5** canonical and **2/4** order exact,
  maximum remaining error 1. No tolerance changed. XG_rush and real components
  were not recaptured; prior pixel failures remain open.
- Retained Rukia numeric-goto regression: **31/31** exact.
- PROTECTED_FUNCTION_OK; integrity/reviewed hashes, handoff and contracts **pass**.
- Final whole-roster replay: **227/227**, **130,334 states** against unchanged
  native baselines; roster.log / roster-report.json.

Full AS/clip-action ownership, all-source placements, deferred context fields,
parent runtime/assets, exact pixels and final whole-build acceptance remain open.
Byakuya 631/985's original narrowly hashed exception is unchanged.

## Reproduce

For each fighter in daitu/minren/sasuke/yihu, using local tool paths and a fresh OUT:

```sh
python3 tools/probes/build_parent_goto_probe.py --fighter "$FIGHTER" \
  --ffdec "$FFDEC" --output "$OUT/$FIGHTER"
python3 tools/probes/capture_native_player.py "$OUT/$FIGHTER" "$OUT/$FIGHTER/native.log" \
  --player-app "$FLASH_APP" --allow-window-activation --timeout 40
python3 tools/importer/audit_parent_forms.py \
  --requirements evidence/importer-loud-fail/r07/parent-form-requirements.json \
  --ffdec "$FFDEC" --output "$OUT/target-audit.json"
python3 tools/importer/audit_frame_calls.py --output "$OUT/frame-calls.json"
python3 tools/importer/audit_shipped_placements.py --output "$OUT/placements.json"
python3 tools/build_online_manifest.py --check
```

Audit/build commands return nonzero while their documented blockers remain.
