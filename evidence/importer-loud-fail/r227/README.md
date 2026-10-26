# r227: independent impulse amplitudes reject a single final-floor weight

Original shape56/57 tags, fill65, masks, matrices and camera are unchanged. Twelve independently generated lossless bitmap55 inputs contain one red corner impulse at64/128/255, with G0/B73/A255. Native capture retains96images/884736RGBA,44160exact source pixels,48matrix groups and both cache-state bounds (48/48 pairs equal).

At amplitude255, red and alpha match the pinned r223 gray impulse references **294912/294912** pixels. Changing the other color channels did not alter that measured red/alpha path. Native references are never source textures.

On70560 geometry-selected deep-interior coordinate triples, native inactive/constant/alpha invariants have0failures;388triples have any nonzero native red. The construction `floor(amplitude * weight / denominator)` has no common weight for206triples at denominator256, and46at65536. All46 also reject a real-valued common weight: native [4,10,19] requires both w<5/64 and w>=5/64. Every coordinate and strict half-open interval is retained. These are rejection intervals, not coefficients selected for rendering. All12 fixed-coordinate interpolation models also remain rejected: the closest active-union result is only19/408 (full total70171/70560), maximum red deltas[7,14,28]. The large zero background must not be interpreted as visual parity.

The46counterexamples constrain operation ordering independently of choosing a coordinate phase. They do not identify an admitted two-stage rule. Full r225/r226 failures remain retained; this geometry subset does not shrink admission.

## Reproduce

```sh
python3 -m tools.probes.build_jinye_red_impulses --output /tmp/bvn-r227/native --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec-cli.jar
# Capture source0..11 sequentially with capture_native_player.py.
python3 -m tools.probes.analyze_jinye_impulse_weights --native evidence/importer-loud-fail/r227/native --output /tmp/bvn-r227/analysis.json
```

Every amplitude constraint and fixed-model residual is retained in analysis.json.gz. Full Python run:1011pass/2skip (1013tests); later focused tests recorded separately. Mandatory gates in acceptance.json/checks. Production runtime unchanged; roster/Web and54production images not rerun. Source-backed diagnostic coverage46/54; historical production9/54. AS/clip-action ownership still open. Candidate/GPU/production admission false.

## Next discriminator

Jointly test four corners and all three amplitudes against fixed vertical-horizontal and horizontal-vertical two-stage interpolation sequences. Footprint cells must be geometry-proved or a predeclared finite set spanning the source corners, including a disjoint state. This is existential rejection only: do not select a cell, phase or coefficient for rendering from native output. Preserve all old/full failures and avoid new captures until this constraint distinguishes sequences.
