# r89 — real Jiraiya fill translation separates from draw initialization

Original Jiraiya DefineShape274 and bitmap273 tags are copied byte-for-byte into an isolated native SWF, verified again after FFDEC compilation. The source-authored single smooth clipped fill,20×20 bitmap matrix with16-twip Y translation, full rectangular mask and3480 original premultiplied texels are retained. Six native RGBA images vary integer/fractional translations and the authored non-binary anisotropic scale; the final case uses the component harness's normalized draw parameters. This is a leaf diagnostic, not the complete filtered54-suite component.

Two **globally fixed** constructions use the unchanged admitted clipped initializer/interpolation:

| Construction | Exact complete native images |
|---|---:|
| Compose fill translation into draw translation before quarter/fixed initialization | 0/6 |
| Initialize inverse draw coordinates, then subtract authored fill translation | **5/6** |

The second leaves only three interior samples in case3 (scale1.23333740234375×1.24481201171875, draw translation4,4):

| Coordinate | Candidate RGBA | Native RGBA |
|---|---|---|
|75,20|56,52,52,127|56,52,52,128|
|75,26|45,42,42,103|45,42,42,104|
|75,27|24,22,22,55|24,23,23,56|

All are at the same near-right source footprint; candidate source X57.47265625, within the60-wide bitmap. Y fractions are not at a byte threshold. This points to independently testing span termination/routing before changing fill coefficients. It does not justify switching arithmetic at these coordinates.

All predicted coverage-fringe samples match **because the source fringe is transparent**: nonzero native fringe alpha count is0 in every case. Therefore coverage arithmetic is **not proven** by this pass. Per-case interior/fringe/outside counts and rejected predictions are retained separately, so large transparent backgrounds cannot hide the residuals.

## Reproduce

```sh
python3 -m tools.probes.build_jiraiya_bitmap_binding --output /tmp/bvn-r89/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r89/native /tmp/bvn-r89/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 45
python3 -m tools.probes.analyze_jiraiya_bitmap_binding --native evidence/importer-loud-fail/r89/native --output /tmp/bvn-r89/recheck.json
python3 -m unittest tools.tests.test_jiraiya_bitmap_binding
```

[Summary](summary.json), full failed coordinates in `analysis.json.gz`, source mask/fill fixture and paired transparent/black readback in `native/`, [hashes](provenance.json), [acceptance](acceptance.json). No old sampler or reference changed; no GPU/production binding.

Next capture independent four-corner impulses and horizontal/vertical ramps at the same60×58 fill/draw transforms, varying clip starts/ends while retaining samples around x75/y20,26,27. Compare full spans and single-pixel clips to distinguish span termination from coordinate arithmetic. Keep fill translation separate and all old sampler controls strict; never infer a selector from whichever formula matches an observed pixel. A separate nontransparent mask-edge control remains necessary for fractional coverage.

`whole_image_admitted=false`, `production_admitted=false`. Historical54-suite remains9/54. JPEG3 Jinye55/Orochimaru340, general coverage/affine/implicit buffers and AS/clip-action ownership remain open. Full roster/Web/54 component renders not rerun. Draft only; no merge/deploy/Worker.
