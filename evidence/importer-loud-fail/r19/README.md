# r19 — integer difference/overlay admitted; 33 of 34 placements cleared

The shared renderer now implements Flash difference (7) and overlay (13) using premultiplied byte arithmetic. A fresh62-SWF export/audit clears all33 blend errors: Kenshin difference1, minrenx overlay1, qilabi overlay30, main root/frame56 overlay1. **DropShadow remains a hard error; no allowlist or pixel tolerance was added.** This PR is still not merge-ready because that filter, existing component/color pixel differences and the complete AS/clip-action audit remain open.

## Runtime change and exact evidence

The earlier floating formulas lost integer information by unpremultiplying colors, blending, and letting the GPU round source-over output. The new path keeps input premultiplied channels `bp/sp` and alpha `ba/sa` in byte units, computes integer numerators, then truncates the final quotient by255. Difference's numerator is:

```
255*(bp+sp) - 2*min(bp*sa, sp*ba)
```

For overlay, start with `base=255*(bp+sp)-bp*sa-sp*ba`. At or below `2*bp <= ba`, add `2*bp*sp`. Otherwise add `sa*ba-2*(ba-bp)*(sa-sp)` and subtract1 when both alphas are nonzero. This reduces to r18's proven opaque formula and preserves transparent endpoints. Output alpha uses the single numerator `255*(sa+ba)-sa*ba`; subtracting separately rounded GPU quotients caused an opaque alpha254 artifact and is not used.

Ordinary raster leaves now use the same native byte-input quantization previously used only inside filters. A rounded backdrop cannot be reconstructed accurately when a later sibling blends against it. Non-normal blend groups cache even a single leaf before applying group opacity: distributing opacity into that leaf quantizes at the wrong stage. The first regression run exposed this ordering issue; it was fixed before final acceptance. Existing regression thresholds and native expectations are unchanged.

Strict native/GPU assertions in `tools/test_integer_blends.py` cover:

- Existing mixed-alpha/group-opacity fixture: **30/30 cases**, previously18/30.
- Fresh alpha ramp: **3,072/3,072 cases**,12,288 RGBA channels. Difference and overlay each match4,608 RGB channels in the independently computed integer model.
- Fresh even-alpha/half-color boundary fixture: **336/336 cases**,1,344 RGBA channels. The original ramp backgrounds had odd alpha153/255, so they did not exercise equality. This probe caught an incorrect high-branch equality before final acceptance; native uses the low branch at exact half.
- Fresh layered backdrop/group-opacity fixture: **192/192 cases**,768 RGBA channels.
- Retained r18 complete opaque overlay grid: **65,536/65,536 pixels**,262,144 RGBA channels.

Every channel must match exactly. These are shared primitive/composition semantics, not a claim that all original component images or full fighter actions are now pixel-identical. The older color/order component gaps remain separately tracked. Ordinary blends' existing legacy regression bound was not broadened and is not used for the new modes.

The alpha-ramp probe records both pre-blend inputs and the output, including direct premultiplied RGB measured by drawing onto black. `beginFill` percentage conversion can yield an alpha byte below the requested integer; the GPU fixture uses the **observed native input byte**, with the requested value retained separately. This matches inputs rather than tuning output expectations. Raw traces and unique SWF/build hashes are retained in `blend-ramp/` and `layered/`.

## Placement audit and guard coverage

[Cleared source locations](cleared-placements.json) retain the exact prior diagnostics, SWF hashes, XML, depths and active frame intervals. They are historical error records, not remaining failures. [Current source audit](source-audit-summary.json) records62 SWFs,26 accepted caches and98 accepted current visual closures. Supported blends become placement obligations in the source catalog; a cached timeline still cannot drop or change them. Unknown blends10/11/12 and other unsupported fields still fail with source locations. Guard tests now use unsupported invert10 instead of newly supported7/13.

The sole remaining source placement is [main.swf, DefineSprite1504/frame1/depth6](remaining-placements.json): text character1503 with black outer DropShadow, blur3×3, strength3, distance1, angle0.7853851318359375 radians. The full inventory still exits1 intentionally. The current shipped closure and Web build are separate gates.

## DropShadow: sharper blocker, not admitted

Fresh136 impulse cases support fixed-point bilinear weighting: truncate the first three weights to1/256 and assign the residual to the fourth. The isolated shader now matches **12/12 original source-parameter cases** exactly, including the three alpha differences of3 from r17.

However, a new256-case matrix also varies negative offsets, source alpha128/255, black/colored shadows, blur0/3 and strength1/3. The best candidate reaches **232/256**, not256/256. The remaining24 failures occur at angles−45°/135° and distance0.125, with channel deltas up to3 after strength multiplication. Adding an epsilon to weight truncation fixes these cases but breaks32 cases elsewhere (224/256); no such adjustment is admitted. This is a floating-point phase/weight-boundary problem, not justification for a tolerance. The best rejected filter patch, raw capture, actual outputs and strict failure report are retained here; neither filter runtime file nor filter admission was changed.

Next experiment: sample single-pixel impulses around the negative diagonal1/8-distance boundary, record native angle/distance getters, and sweep both values across the weight transition. Resolve native coordinate/weight precision before admitting the shared DropShadow path. Matching the one authored positive offset does not prove that path correct in general.

## Source-first scope

1. All33 source locations/XML are linked above. This change adds display compositing only; original frame scripts and enterFrame callbacks are unchanged. Synthetic probes stop on their only frame and explicitly construct the measured display list.
2. PlaceObject/MOVE replacement, filter inheritance and lifetimes remain governed by the existing source-hashed placement guards. Admission creates required blend fields rather than stripping them.
3. Label exits, playback clocks, callback ownership and body replacement are unchanged.
4. The invariant is native premultiplied byte output, including zero alpha, layered backgrounds and parent opacity. No expected channel or comparison bound was changed to green a candidate.
5. Flash Player Debugger32.0.0.465/Rosetta is the reference; Godot4.7.2 Compatibility supplies actual pixels. Whole-roster state replay is a separate acceptance gate. No intentional fidelity/stability deviation was introduced.

## Reproduce

Use local `FFDEC`, `FLASH_APP`, `GODOT`, and fresh scratch `OUT` paths. Probe output must not overwrite locked inputs.

```sh
python3 tools/probes/build_flash_filter_probe.py --case blend-alpha-ramp --output "$OUT/blend-ramp" --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py "$OUT/blend-ramp" "$OUT/blend-ramp/native.log" --player-app "$FLASH_APP" --allow-window-activation --timeout 40
python3 tools/probes/decode_placement_math_capture.py --kind ramp --build "$OUT/blend-ramp/build.json" --trace "$OUT/blend-ramp/native.log" --output "$OUT/ramp.json"
# Repeat with case blend-alpha-boundaries / kind boundary; blend-layered / kind layered; shadow-impulse / kind impulse;
# drop-shadow-extended / kind extended (timeout60 for the extended capture).
python3 tools/test_integer_blends.py --godot "$GODOT" --output "$OUT/integer-blends"
# Exit0:30 +3072 +336 +192 +65536 exact cases/pixels; any changed channel fails.
python3 tools/importer/audit_importer.py --ffdec "$FFDEC" --output "$OUT/source-audit.json" --write-placement-requirements tools/importer/placement_requirements.json
# Exit1: one DropShadow source error;26 caches and98 current closures pass.
```

To reproduce the rejected shadow candidate, copy `godot/` including its imported cache into an isolated `$OUT/candidate/godot`, apply `rejected-shadow-candidate.patch` from that copy's root with `git apply --unidiff-zero`, decode `extended/native.log` with kind `extended`, run `tools/probes/drop_shadow_candidate.gd` against that copied project, then compare with `compare_placement_candidates.py --kind shadow`. The strict comparator must exit1:232/256. Run against `drop-shadow-native.json` for12/12 exact. The patch must not be applied to production.

## Final acceptance

See `acceptance-summary.json` and adjacent logs for completed final runs. Initial candidate failures are retained separately and are not reported as final acceptance. Full local Web build does not deploy to Vercel or production. No merge, Worker change or new character port.

Final runs: roster **227/227**,130,334 states; Python **492 passed +2 skipped**; GPU **7/7**,Godot **22/22**; exact blur **242/242**,legacy blend **38/38**. Protected, reviewed integrity hashes, handoff, contracts, fingerprint tests **8/8**, full local Web export and post-export manifest/metadata checks all pass. Source inventory intentionally remains exit1 for DropShadow; merge acceptance remains incomplete.
