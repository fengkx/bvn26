# r17 — placement lifetime guards and rejected native candidates

**0 of34 source placement errors cleared.** They remain hard failures: difference1, overlay32, DropShadow1. No approximate renderer, allowlist or tolerance was admitted. This is a checkpoint, not merge-ready completion.

## What landed

- A rejected placement field now retains its source interval through subsequent display frames. A slice starting *after* the original bad PlaceObject/MOVE can no longer bypass that error while the field remains active. An unrelated MOVE preserves the rejection; an explicit field overwrite, removal or new placement ends the appropriate interval. Even a failed MOVE replaces the fields it explicitly writes while independently recording its new failures.
- The inventory reports independent field/blend/filter diagnostics together, with depth, resolved character ID, MOVE status and last active frame. A bad blend cannot hide a bad filter.
- The full-source audit uses the current form-aware compilation/cache contracts, instead of compiling admitted form graphs as base-only contexts and reporting false failures.
- Native capture builders/fixtures, exact comparators and rejected candidate patches are reproducible. Repeated filter captures receive unique run IDs. One-channel differences fail regression comparison.

## Why the renderers were not admitted

`blend-comparison.json` records30 native cases. Native pre-blend pixels distinguish input raster quantization from compositing. Premultiplied output RGB is measured by drawing the captured BitmapData onto black; reconstructing it from getPixel32 would lose bits. The standard floating difference candidate is exact8/15 (other cases differ by1); overlay is exact3/15 (up to3). Overlay already differs for opaque controls, so this cannot be dismissed as transparent-output readback. The missing work is Flash's integer input/composition arithmetic and its interaction with the existing backdrop raster. Formula-only support would silently change these placements.

`shadow-comparison.json` samples all32×32 pixels in12 cases with the actual source's black outer shadow, blur3×3, strength3, passes1. Integer-axis controls pass. Nearest-pixel translation misses43 pixels in the authored approximately45°/distance1 case. Bilinear translation with quantized alpha improves that case to **3 differing alpha channels, each by3**; the distance5 diagonal has2 differing alpha channels. Thus10/12 cases and49,147/49,152 RGBA channels match, which is still a failure. Fractional displacement/rasterization and quantization order remain unresolved; the evidence does not establish a replacement algorithm.

Both patches under `rejected-*-candidate.patch` are **outside production**. They are measurements of rejected implementations, not runnable shipping support. Existing runtime/generated fighter assets are unchanged. These isolated primitive probes do not constitute real-component image parity or new character ports.

## Source-first scope

1. The new rendering experiments contain only a stopped synthetic frame, explicit clip construction and BitmapData sampling; no combat, goto or enterFrame semantics are added. The source inventory identifies each original SWF, sprite/frame, depth and authored XML in `remaining-placements.json`.
2. New versus MOVE semantics and explicit field overwrites are tracked directly from PlaceObject/RemoveObject/ShowFrame. Rejected state persists without an overwrite; interval tests exercise later-frame-only slices.
3. Label exits and body clocks are unchanged. No runtime candidate was admitted.
4. Native observations, not candidate outputs, define the oracle. Every channel must match; no tolerance is used.
5. Native Flash Debugger32.0.0.465 under Rosetta captured the parameter probes. Full original-component image parity was not established, and the source guards remain closed for that reason.

## Acceptance and remaining work

Production regression acceptance: **227/227 replay,130,334 states; Python484 passed+2 skipped; GPU7/7; Godot22/22; PROTECTED_FUNCTION_OK, integrity, handoff, contracts and fingerprint8/8 all pass. Caches26/26 and shipped placements98/98. Full local build_web exits0, including post-export fingerprint and WEB_BUILD_METADATA_OK.** This does not turn the rejected native candidates or full source inventory green. See [acceptance](acceptance-summary.json), [source summary](source-audit-summary.json), [remaining placements](remaining-placements.md), and the adjacent logs. The full62-SWF scan is followed by re-export of the four failing SWFs after refining per-field retirement; all62 source hashes are rechecked. The full inventory intentionally exits nonzero for34 unsupported placements. The current shipped closure, cache and Web build results are separate acceptance gates.

Still open: all34 placements, existing exact color/order/XG_rush/component pixel differences, and the full AS/clip-action semantic ownership audit. No merge, production deploy, Worker change or new port.

## Reproduce native measurements

Set `FFDEC`, `GODOT`, `FLASH_APP`, and `OUT` to local paths; run from the repository root. Native probes require a fresh output directory.

```sh
python3 tools/probes/build_placement_blend_probe.py --output "$OUT/blend" --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py "$OUT/blend" "$OUT/blend/native.log" --player-app "$FLASH_APP" --allow-window-activation --timeout 40
python3 tools/probes/build_flash_filter_probe.py --case drop-shadow --output "$OUT/shadow" --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py "$OUT/shadow" "$OUT/shadow/native.log" --player-app "$FLASH_APP" --allow-window-activation --timeout 40
```

To reproduce the rejected candidates, copy `godot/` including its imported cache into an isolated `$OUT/candidate/godot` (never patch the shipping worktree), apply the respective patch from `$OUT/candidate`, and run the probe against that copied project:

```sh
REPO="$PWD"
mkdir -p "$OUT/candidate"
cp -R godot "$OUT/candidate/godot"
(cd "$OUT/candidate" && git apply --unidiff-zero "$REPO/evidence/importer-loud-fail/r17/rejected-blend-candidate.patch")
"$GODOT" --path "$OUT/candidate/godot" --rendering-method gl_compatibility --script "$REPO/tools/probes/placement_blend_candidate.gd" --log-file "$OUT/blend-engine.log" -- "$REPO/tools/probes/flash_filters/placement-blend-native.json" "$OUT/blend-candidate.json"
python3 tools/probes/compare_placement_candidates.py --kind blend --native tools/probes/flash_filters/placement-blend-native.json --actual "$OUT/blend-candidate.json" --output "$OUT/blend-comparison.json"
# Comparison must exit1:11/30 exact. Apply the shadow patch to a fresh copy,
# run drop_shadow_candidate.gd with drop-shadow-native.json, then compare
# with --kind shadow. That comparison must exit1:10/12 exact.
```

Production acceptance uses the unchanged GPU/Godot suite from r16 (`GODOT="$GODOT" OUT="$OUT" python3 evidence/importer-loud-fail/r16/godot/commands.py`), full roster replay, Python discovery, protected/integrity/handoff/contracts, online manifest check and full local build_web. Raw candidate captures and failed comparisons are retained separately from these production checks.
