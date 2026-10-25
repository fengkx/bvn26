# r96 — outer scale disproves truncating child translation

540 independent native controls retain480 explicitly verified source texels and every child/outer/composed matrix property. Outer horizontal scale0.5/1/1.5/2/3, signed child and outer origins vary independently; y interpolation remains integral and each destination sample has a1×1 clip.

- Direct-composed initializer: **83423/83423** interior RGB samples exact.
- r95 separate-quarter truncation:52769/83423. All30654 failures occur at outer scale3; it cannot be generalized.
- Independently fixed common construction: **multiply child translation by outer scale, round to nearest quarter pixel, then add the separately toward-zero-quarter-consumed outer draw translation**. Both ties-even and ties-away versions match **83423/83423**, and retain all old r95 nested controls **26538/26538**. The current origins do not distinguish exact-half ties.
- Quantizing the child before scale or retaining the raw outer draw translation does not explain all controls. Full competing-model failures and excluded boundary pixels are retained.

No per-pixel path or coefficient is selected from RGB. The old r95 source-bound success remains valid within its unit-outer-scale domain; no claim that its initial truncation hypothesis was general. The scalar sampler itself is unchanged.

The first one-frame expanded capture stopped without `done` after1528 events and was rejected. The successful capture splits independent outer-scale groups across enterFrame callbacks, with identical source/transform grids and no animation. Complete1629-event capture is required. Incomplete log, original harness and hashes remain under `initial-incomplete/`; it contributes no acceptance count.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-nested-scale --output /tmp/bvn-r96/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r96/native /tmp/bvn-r96/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 60
python3 -m tools.probes.analyze_bitmap_nested_scale --native evidence/importer-loud-fail/r96/native --output /tmp/bvn-r96/analysis.json
python3 -m unittest tools.tests.test_bitmap_nested_scale
```

[Summary](summary.json), complete comparisons in `analysis.json.gz`, [hashes](provenance.json), [acceptance](acceptance.json).

Next discriminator: signed child translations and outer scales yielding exactly ±0.125/±0.375 pixel, plus immediate neighboring authored twip values. Retain both source matrix properties and direct draw controls. Distinguish ties-even/away with one common construction and retain every old control before GPU wrapper work. No production enablement from these bounded scalar tests.

`production_admitted=false`; complete54-suite historical9/54. Original full filtered components, general affine/coverage, implicit boundaries and AS ownership remain open. Draft only; no merge/deploy/Worker.

Fresh Python732 pass +2skip; caches26/26, fingerprint, protected, integrity, handoff/contracts green. Full roster/Web not rerun: production unchanged.
