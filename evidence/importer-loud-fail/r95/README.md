# r95 — independent nested-translation controls clear the held-out wrapper input

180 independent controls use an explicitly read-back60×8 opaque bitmap (alternating red, unique green ramp, constant blue), four child scales, five signed child origins and nine positive outer translations around twip/quarter boundaries. Child, outer and composed matrix properties are retained. Every output uses a separate1×1 clip at y7; source vertical fraction is zero.480 original texels verify exactly. Boundary/outside pixels are retained separately; only the full interior constrains interpolation.

- Direct composed draw: existing common scalar initializer **26538/26538 exact**.
- Nested draw with the same double composed translation:21819/26538; **4719** independent samples differ between native nested/direct paths.
- Consume child and outer translations separately toward zero on the quarter-pixel grid, then compose: **26538/26538 exact**.
- Consume only child translation first, then let the scalar initializer consume the combined translation: also26538/26538. These constructions are observationally equivalent on the present positive-outer/unit-outer-scale domain; **not yet uniquely identified**.
- Nearest-twip rounding does not explain the nested samples (21229/26538). Full failures retained; no per-pixel route selection.

Only after these independent controls, the separate-quarter construction is applied unchanged to the held-out original r93 Jiraiya cleared wrapper. It resolves the old1767-pixel discrepancy: **240000/240000 premultiplied RGBA pixels exact**. Source metadata yields effective draw translation263/162.75 with the unchanged authored scales, fill and mask. Nontransparent fractional edge footprints still reject. This is an unfiltered input-boundary proof, not complete authored Blur or production admission.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-nested-translation --output /tmp/bvn-r95/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r95/native /tmp/bvn-r95/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 60
python3 -m tools.probes.analyze_bitmap_nested_translation --native evidence/importer-loud-fail/r95/native --output /tmp/bvn-r95/analysis.json
python3 -m unittest tools.tests.test_bitmap_nested_translation
```

[Summary](summary.json), complete competing-model failures/boundary readbacks in `analysis.json.gz`, [hashes](provenance.json), original log/property readbacks in `native/`, [acceptance](acceptance.json).

Next discriminator: independently vary outer horizontal scale and positive/negative outer translations while retaining child matrix/property controls. Separate “quantize each node before composition” from “quantize the child then combined draw”; require all current and old controls before widening the candidate or binding GPU wrapper filters. Do not pick the construction by a source image's RGB.

`production_admitted=false`; historical54-suite9/54. Full authored filters, general affine/coverage, implicit boundaries and AS ownership remain unproven. Draft only; no merge/deploy/Worker.

Fresh Python730 pass +2skip; caches26/26, fingerprint, protected, integrity, handoff/contracts green. Full roster/Web not rerun: production unchanged.
