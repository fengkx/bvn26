# r179 — original main nearest leaf interior exact, storage paths retained

Original main.swf Bitmap281/Shape282 tags are copied byte-for-byte into an isolated leaf diagnostic. The original fill67,137×200 rectangle mask and fill matrix remain intact. The authored owner298 frame1 matrix is decoded from its binary placement, not approximated from rounded XML text. No production SWF or wrapper reference is rewritten.

Before/after loadBitmap images match **480000/480000 pixels**. Original format3 versus an AS-created bitmap filled from explicit readbacks also match **480000/480000 full-image pixels**. All27400 source texels match the source extraction, including20979 transparent pixels; source alpha is binary.

The shared rounded nearest construction matches geometry-selected interiors **52921/52921** for each storage path (26730 unit,26191 original affine). Selection uses mask geometry alone, never native color/alpha. Transparent holes participate in the strict RGBA comparison.

This is not a complete image gate:3 nonzero unit-transform pixels and12 nonzero affine pixels remain outside the proved interior. Their exact coordinates/RGBA are in `unproven_nonzero_pixels`; every excluded pixel, including zero pixels, remains outside the sampler claim. Arbitrary coverage, full filter/CXFORM/cache allocation and production composition remain separate.

[Summary and remaining coordinates](summary.json), [native source/fill/mask fixture](native/fixture.json.gz), [native capture](native/native.log.gz), [images](images/), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.build_nearest_component_input --output /tmp/nearest-main-input --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/nearest-main-input /tmp/nearest-main-input/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_nearest_component_input --native evidence/importer-loud-fail/r179/native --output /tmp/nearest-main.json
python3 -m unittest tools.tests.test_nearest_component_input
```

Next discriminator: bind these original raw texels and geometry to the admitted integer GPU diagnostic, compare only the explicitly marked proved interior, and retain all15 nonzero edge coordinates as unresolved. Then isolate constant-color affine mask coverage independently before attempting a complete leaf or wrapper gate. Do not turn an interior mask into production eligibility or count it as a54-suite image.

`source_sampler_admitted=false`, `production_admitted=false`, `full_production_suite_rerun=false`. Production54 remains historical9/54;24 prior complete live/wrapper diagnostics exact. Full AS ownership remains open. Draft only.
