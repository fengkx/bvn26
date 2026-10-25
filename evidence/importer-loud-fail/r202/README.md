# r202 — coefficient property brackets reject an identity-only explanation

Capture27 coefficients around0.5/1/2 at1/8192 spacing, all256 source green bytes and both adjacent-alpha contexts. All55296 explicit source pixels and13824 matrix properties verify; all13824 G/B/A target identity outputs remain exact. The matrix routes green into red, so the enclosing transform is never identity.

With a transparent neighbor, coefficients from1−4/8192 through1+2/8192 produce the same complete red ramp as coefficient1. Coefficients1+3/8192 and1+4/8192 share another ramp. Thus the copy-like result is not unique to the exact identity coefficient. This plateau is an observation, not proof of a coefficient storage format or a special branch.

With an opaque neighbor, the0.5 ramp changes between0.5−3/8192 and0.5−2/8192; finer properties themselves remain distinguishable in readback. Plain multiply, half-input multiply and their shared fixed-precision variants all reject these controls. Best retained candidate12771/13824. Fixed11/half-input12517/13824, despite its4602/4608 r200 crossing: do not admit it from that local score. [All ramps and counterexamples](summary.json.gz), [native](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case matrix-coefficient-brackets --output /tmp/matrix-coefficient-brackets --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/matrix-coefficient-brackets /tmp/matrix-coefficient-brackets/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 120
python3 -m tools.probes.analyze_matrix_coefficient_brackets --native evidence/importer-loud-fail/r202/native --output /tmp/matrix-coefficient-brackets.json
python3 -m unittest tools.tests.test_matrix_coefficient_brackets
```

Next discriminator: retain these coefficient/property brackets while independently shifting output offsets through fixed binary quarter-byte values, holding explicit source bytes and pair-alpha geometry fixed. Distinguish coefficient-consumption plateaus from final rounding plateaus; do not assume offset consumption from CXFORM or compare separately materialized operations as equivalent. Retain r200/r201 controls and reject any construction against original materialized native boundaries before GPU.

Arithmetic/GPU/production admission false. Main family10/12; identity2953 differing pixels,maxdelta1; production54 historical9/54. Full AS ownership remains open. No runtime changes, merge or deployment.
