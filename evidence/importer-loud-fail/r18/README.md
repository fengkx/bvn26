# r18 — exact opaque overlay arithmetic; alpha sampling still blocks admission

**0/34 source placements cleared.** Difference ×1, overlay ×32 and DropShadow ×1 remain hard errors. No runtime code, generated production assets, allowlists or comparison tolerances changed. This checkpoint advances the native arithmetic diagnosis; it is not merge-ready.

## New measured results

| Experiment | Exact result | Interpretation |
|---|---:|---|
| Opaque overlay, every byte pair | 65,536/65,536 pixels, 262,144/262,144 RGBA channels | Native Flash and isolated GPU candidate agree |
| Existing mixed-alpha difference/overlay probe, integer overlay candidate | 18/30 cases (r17: 11/30) | Difference 8/15, overlay 10/15; maximum remaining channel delta 2 |
| Same probe, additionally quantizing leaf inputs and removing blend leaf shortcut | 17/30 cases, remaining delta 1 | Applying cached-input quantization alone does not solve compositing |
| DropShadow mask, strength1, hideObject, blur3 | 9/12 cases | Diagonal distances1/2/5 have 7/3/4 alpha differences, each1 |
| DropShadow mask, strength1, hideObject, blur0 | 9/12 cases | Diagonal distances1/2/5 have 30/30/32 alpha differences, each1 |

The complete opaque grayscale grid establishes this byte-channel formula (background `b`, source `s`):

```python
2 * b * s // 255 if b < 128 else 254 - 2 * (255-b) * (255-s) // 255
```

The high branch's254 and integer truncation explain the opaque endpoint errors. `analyze_placement_arithmetic.py` retains this as a **diagnostic model**, with a regression against all native samples. It is not production support. The scratch GPU candidate implements the same arithmetic through the existing shared blend shader; no character-specific branches are involved. Its full-opacity grid is exact, but real placements can have translucent raster/edge pixels, so opaque parity cannot justify admitting any of the32 overlay errors.

The mixed-opacity probe still fails: e.g. case16 expects `[99,96,176,224]`, candidate gives `[101,97,176,224]`; difference case2 expects `[101,63,119,255]`, candidate gives `[102,64,119,255]`. Even opaque source fills with50% group opacity can differ. Native cached fill quantization, unpremultiplication and final source-over arithmetic must be resolved together. Forcing the existing cached-input quantizer and removing the single-leaf blend shortcut reduced some deltas but regressed other cases:17/30. Neither patch is admitted.

DropShadow mask probes remove two confounders from r17: source-over coverage and strength3 saturation. The blur0 probe still disagrees with ordinary bilinear translation, so changing only blur order cannot solve the defect. At the source's approximately45°/distance1 offset, native's leading corner alpha is20 versus bilinear21; its edge is73 versus74, while the opposite edge is181 versus180. With blur3, the same case has seven differing samples before strength/source composition. R17's original source-parameter candidate remains10/12 exact, including three alpha deltas of3 in the authored case; this was not reclassified as passing.

**Next experiments:** capture a one-pixel alpha impulse across fractional offsets and input alpha levels to identify native resampling weights/rounding independently of blur. For blends, measure pre-blend premultiplied inputs and output across alpha ramps, including leaf versus explicit cached group, before changing shared source-over arithmetic. The evidence identifies unresolved integer stages; it does not establish that exact parity is impossible.

## Reproducibility correction

The r17 blend fixture stored native readback arrays over the authored `back`/`front` integer colors. The historical candidate was measured with the original build's input cases, but the documented command using the checked-in fixture could not reproduce it. `decode_placement_blend_capture.py` now keeps inputs and readbacks separate and requires a complete, ordered capture. All30 native premultiplied expectations are **unchanged**, verified in `fixture-migration.json`; no reference output was tuned to the candidate. The existing candidate runner now consumes the checked-in fixture directly. Rebuild the corrected fixture from retained r17 evidence with:

```sh
python3 tools/probes/decode_placement_blend_capture.py --build evidence/importer-loud-fail/r17/blend-build.json --trace evidence/importer-loud-fail/r17/blend-native.log --output "$OUT/placement-blend-native.json"
```

The native source hashes/environment remain Flash Player Debugger32.0.0.465/Rosetta, JPEXS26.2.1 and Godot4.7.2 Compatibility. Fresh native traces, build hashes and capture metadata are in `grid/`, `shadow-mask/`, `shadow-offset/`. Neither synthetic fixture changes a locked game/scripts file.

## Source-first scope and remaining sites

1. These are stopped, single-frame synthetic BitmapData/filter probes with no gameplay callbacks. The original source locations and XML remain in [r17 remaining placements](../r17/remaining-placements.md).
2. Production PlaceObject/MOVE lifetimes and guard contracts are unchanged; no subset is inferred harmless from opaque test inputs.
3. Label exits, playback clocks and body state are unchanged.
4. Native samples define every expected byte. A one-channel mismatch fails comparisons.
5. Opaque grayscale parity is established; mixed-alpha and real-component parity are not. All34 guards remain closed.

The exact remaining inventory is unchanged: Kenshin2506/frame568 difference; minrenx449/frame382 overlay; qilabi766's30 overlay sites; main root/frame56 overlay; main1504/frame1 DropShadow. See r17 JSON for hashes, depths, character IDs and active frame intervals. Existing color/order/XG_rush/component differences and the full AS/clip-action ownership audit remain open.

## Reproduce

Set `FFDEC`, `GODOT`, `FLASH_APP`, `OUT` to local tools/scratch paths. Native capture needs a fresh output directory and window activation. No production deployment is involved.

```sh
python3 tools/probes/build_flash_filter_probe.py --case placement-overlay-grid --output "$OUT/grid" --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py "$OUT/grid" "$OUT/grid/native.log" --player-app "$FLASH_APP" --allow-window-activation --timeout 40
# Repeat with --case drop-shadow-mask and --case drop-shadow-offset.

REPO="$PWD"
mkdir -p "$OUT/candidate"
cp -R godot "$OUT/candidate/godot"
(cd "$OUT/candidate" && git apply --unidiff-zero "$REPO/evidence/importer-loud-fail/r18/rejected-blend-candidate.patch")
"$GODOT" --path "$OUT/candidate/godot" --rendering-method gl_compatibility --script "$REPO/tools/probes/placement_overlay_grid_candidate.gd" -- "$OUT/grid-candidate.json"
python3 tools/probes/analyze_placement_arithmetic.py --kind overlay --build "$OUT/grid/build.json" --trace "$OUT/grid/native.log" --gpu "$OUT/grid-candidate.json" --samples "$OUT/grid-samples.json" --report "$OUT/grid-comparison.json"
# Exit0, no different channels.
"$GODOT" --path "$OUT/candidate/godot" --rendering-method gl_compatibility --script "$REPO/tools/probes/placement_blend_candidate.gd" -- "$REPO/tools/probes/flash_filters/placement-blend-native.json" "$OUT/blend-candidate.json"
python3 tools/probes/compare_placement_candidates.py --kind blend --native tools/probes/flash_filters/placement-blend-native.json --actual "$OUT/blend-candidate.json" --output "$OUT/blend-comparison.json"
# Exit1:18/30, not passing support.
python3 tools/probes/analyze_placement_arithmetic.py --kind shadow-mask --build "$OUT/shadow-mask/build.json" --trace "$OUT/shadow-mask/native.log" --samples "$OUT/shadow-mask.json" --report "$OUT/shadow-mask-comparison.json"
# Exit1:9/12. Repeat with shadow-offset; also exit1:9/12.
```

The second rejected patch (`rejected-quantized-candidate.patch`) applies to a fresh production copy, not on top of the first patch. Run the same mixed-opacity probe/comparator; expected failure17/30. A failed probe is never runtime admission.

## Production acceptance

**This run: Python487 passed+2 skipped; caches26/26; shipped closures98/98; PROTECTED_FUNCTION_OK; integrity/handoff/contracts; fingerprint8/8; full local build_web exit0, clean import/export scans, post-export fingerprint and WEB_BUILD_METADATA_OK.** Source inventory still34 errors. See `acceptance-summary.json` and adjacent logs. Runtime/importer admission logic and generated assets were not changed; full roster and the production GPU/Godot suite were not rerun in r18. Their r17 results remain historical evidence, not new runs. New GPU candidate measurements are reported separately above. Caches, shipped placement closures, Python, protected function, integrity, handoff, contracts, online manifest/fingerprint and the full local Web build are rechecked for this checkpoint. Draft PR stays unmerged; no deployment, Worker change or new port.
