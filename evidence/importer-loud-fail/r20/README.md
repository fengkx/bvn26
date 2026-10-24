# r20 — DropShadow subpixel phase

The r19 candidate computed bilinear weights from an unquantized floating displacement. Native Flash first rounds displacement to a 1/256-pixel phase. The shared candidate now quantizes each component with `sign(offset)*floor(abs(offset)*256+0.5)/256` (nearest, ties away from zero), then truncates the first three bilinear weights to integer /256 units and assigns the residual to the fourth. It shifts the blurred alpha before strength/color and source-over composition. This removes r19's inconsistent rounding at negative diagonal distances 0.125 and 1 without an epsilon or channel tolerance.

## Native evidence and scope

- New 48-case phase probe records filter angle/distance getters and perturbs distances by ±0.000001. All 48 impulse images match the phase model.
- New 520-case sweep covers eight angles (including non-diagonal ones) and 65 distances. All 520 impulse images match.
- A further 48-case positive/negative half-phase boundary probe exposed the tie rule: negative midpoints round away from zero. All 48 now match; an additional full-image midpoint suite passes **256/256**.
- Production GPU comparison: original source-parameter fixture **12/12**, extended fractional-offset/blur/strength/color/source-alpha fixture **256/256** exact. The strict comparator checks all RGBA channels, not only alpha.
- Raw native traces, build hashes, normalized fixtures and strict comparison reports are retained. Existing r19 reference outputs are unchanged.

Production support is outer, non-knockout, source-composited DropShadow. Inner shadows, knockout and hidden source remain explicit source-location errors. No new allowlist, per-character branch, pixel tolerance or intentional stability deviation.

## Source-first boundary

1. The remaining authored site is `game/main.swf/DefineSprite_1504/frame_1/depth_6`, text character1503, original SWF SHA256 `707fac0ec6bb2af1a3d18dc308dd403cb556a0988144b0f6f10555382287f92d`. Full PlaceObject3 XML is retained in r19/remaining-placements.json. No frame script or enterFrame logic is modified.
2. This is a new placement, not MOVE. Existing placement lifetimes, inheritance and cached obligations remain unchanged; admission preserves all compiled filter parameters.
3. No label exit or timeline clock changes. Synthetic native fixtures stop on their sole frame, build display objects, draw BitmapData and quit.
4. The invariant is exact native premultiplied RGBA after blur, offset, strength/color and source composition, including negative fractional displacement. The production filter shares the existing blur and Glow infrastructure.
5. Adobe Flash Player Debugger32/Rosetta supplies raw pixels. GPU assertions exercise the actual shared Godot renderer. This is filter primitive parity, not proof of full original text rasterization or complete component images.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case shadow-phase --output "$OUT/phase" --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py "$OUT/phase" "$OUT/phase/native.log" --player-app "$FLASH_APP" --allow-window-activation --timeout 40
python3 tools/probes/analyze_shadow_phase.py --build "$OUT/phase/build.json" --trace "$OUT/phase/native.log" --count 48 --output "$OUT/phase.json"
# Repeat shadow-phase-sweep with count520 and shadow-phase-ties with count48.
# Build/capture drop-shadow-ties, then decode with:
python3 tools/probes/decode_placement_math_capture.py --kind extended --build "$OUT/ties-extended/build.json" --trace "$OUT/ties-extended/native.log" --output "$OUT/ties-extended.json"
python3 tools/test_drop_shadow.py --godot "$GODOT" --output "$OUT/shadow"
python3 tools/test_integer_blends.py --godot "$GODOT" --output "$OUT/blends"
python3 tools/importer/audit_importer.py --ffdec "$FFDEC" --output "$OUT/source-audit.json" --write-placement-requirements tools/importer/placement_requirements.json
```

Final acceptance and inventory counts are recorded in acceptance-summary.json. Existing exact color/order/XG_rush/component image differences and full AS/clip-action audit remain separate merge blockers. No merge, deployment, Worker change or new character port.

Full-suite reproduction uses the existing runner: `GODOT="$GODOT" OUT="$OUT" python3 evidence/importer-loud-fail/r16/godot/commands.py`, plus `python3 tools/test_importer_roster.py --godot "$GODOT" --output "$OUT/roster"`, Python unittest discovery, verify/handoff/contracts, online manifest/fingerprint checks and `GODOT_BIN="$GODOT" TEMPLATE_DIR="$TEMPLATES" bash tools/build_web.sh`.

## Final acceptance

Final-code runs: roster **227/227**,130,334 states; Python **496 passed +2 skipped**; GPU **7/7**,Godot **22/22**; blur **242/242**; legacy blend **38/38** and all five r19 strict blend groups pass. **PROTECTED_FUNCTION_OK**, reviewed manifest integrity, handoff, contracts, fingerprint unit tests **8/8**, full local Web build exit0 and post-export manifest/metadata checks all pass. Source inventory is zero placement failures across62 SWFs, caches26/26 and current closures98/98; overall semantic audit remains incomplete.
