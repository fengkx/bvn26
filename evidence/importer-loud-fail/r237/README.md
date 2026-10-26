# r237: outward ShapeBounds changes do not change these cached pixels

Patch only one existing signed RECT field at a time in original nearest67 shape56/57 tags. Baseline plus outward expansions1,20,80twips on each of xmin/xmax/ymin/ymax gives13variants. All nBits15 widths, tag lengths, headers and every fill/mask byte remain unchanged. Expanded bounds conservatively enclose original geometry. Original C/outer, scale1/4 and r236 integer camera remain fixed, both cache states.

13nativefixtures/52images/3407872rawRGBA;47840source pixels and26matrix readbacks verified. Independent bit review confirms all26tag changes. Original baselines match r236 rawcases6/18 in both cache states: **4/4**,262144/262144raw and black pixels, bounds and matrix readbacks exact.

All48nonbaseline variant comparisons are exact: **3145728/3145728** fullpixels and26184/26184deep pixels, independently in rawRGBA and black-composited output. Every one of these48pairs has changed native getBounds values. This does not support deriving a changed sampling origin from those values.

The existing cache difference persists unchanged:13/26cache pairs exact; shape57 at(129,73) is raw[106,84,73,255] uncached versus[108,84,73,255] cached in all13variants. These13deep differences are retained. Metadata-only bounds expansion does not explain r236 shear-factorization differences. No universal claim about bounds or internal allocation follows.

## Reproduce

```sh
python3 -m tools.probes.build_jinye_bounds_controls --output /tmp/bvn-r237/native --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec-cli.jar
# Capture bounds0 through bounds12 sequentially with capture_native_player.py.
python3 -m tools.probes.analyze_jinye_bounds_controls --native evidence/importer-loud-fail/r237/native --output /tmp/bvn-r237/analysis.json
python3 -m unittest tools.tests.test_jinye_bounds_controls tools.tests.test_jinye_bounds_comparison
```

Focused6/6 and mandatory gates recorded. FullPython1059pass/2skip retained fromr235; exact axis suites retained fromr229. No production/GPU change or new roster/Web/54production run. Diagnosticcomplete46/54,historicalproduction9/54. Alladmissionfalse; AS/clip-action ownership remains open.

## Next discriminator

Keep original fill/mask/child transforms and exactly equal final stage geometry, but replace shear factors with predeclared axis factors S=I,diag(2,1),diag(1,2),diag(2,2). Encode F'=S F,mask'=S mask,C'=C inverse(S); integer source fields and float32 display coefficients remain exact. Retain raw original nearest67 and identity-reencoding baselines, scale1/4, bothcache states, and full/deep raw/black comparisons. This isolates axis rescaling from nonorthogonal shear without choosing a sampler formula from output. Do not infer cache allocation from cacheAsBitmap or getBounds alone.
