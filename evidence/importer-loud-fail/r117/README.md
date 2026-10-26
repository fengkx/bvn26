# r117 — held-out fractional geometry preserves cache interiors, exposes endpoint controls

The r116 separate-geometry/translation rule is unchanged. Fresh controls use four new minima, three fractional/integer widths, five scales (including non-binary native matrix values), four child translations and two independently varied outer translations. Each group draws fresh cache-only and alpha-reveal instances. All480 source texels, matrices/bounds and original row/column bytes are retained.

Predicted alpha support is **464/480 exact**. All16 counterexamples are right edges for minimum-1.05/width1.25 at scales0.75 or7.5, across all child/outer translations. Left edges remain480/480 exact. Their public transformed bounds indicate a different consumed endpoint than the mathematical decimal sum; that explanation requires independent local geometry readback and is not patched into this result.

Using the source-derived left origin with unchanged r112 arithmetic, cache-only interior RGB is **29494/29494 exact**. Interior sampling excludes shape/source edges using geometry, not RGB. Narrow shapes have no admitted interior samples; they remain covered by the support checks. No origin is selected from the native output. General allocation, fractional coverage and cache/filter equivalence are not established.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-cache-support-heldout --output /tmp/bvn-r117/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r117/native /tmp/bvn-r117/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 60
python3 -m tools.probes.analyze_bitmap_cache_support_heldout --native evidence/importer-loud-fail/r117/native --output /tmp/support-heldout.json
python3 -m unittest tools.tests.test_bitmap_cache_support_heldout
```

[Summary with all16 counterexamples](summary.json), original bytes in `analysis.json.gz`, [provenance](provenance.json), [acceptance](acceptance.json).

Next discriminator: read local geometry before applying any transform, retaining identical input and rendered rows. Test the unchanged bounds rule using those independently measured consumed endpoints; separately compare a common AS2-to-twip endpoint conversion against every local readback. Then validate the origin construction against all old cache suites before GPU work. No epsilon or special case for the decimal sum is allowed.

`source_cache_initializer_admitted=false`, `production_admitted=false`. Historical components9/54; full AS/clip-action ownership still open. Draft only; no merge/deploy/Worker.

Validation: focused Python2/2; prior r115 full771 pass+2skip retained. Fresh caches26/26, fingerprint, protected, integrity/handoff/contracts green. No runtime change; roster/Web and GPU/component renders not rerun.
