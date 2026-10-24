# r79 — native API identity explains the half-phase counterexamples

288 independent no-blur/unit-gain impulse controls compare explicit `BitmapData.applyFilter`, a filtered bitmap display object and a filtered vector display object. Both unfiltered source readbacks are exact (**28224/28224 RGBA samples**). The same input and filter parameters are retained across paths.

| Global phase rule | applyFilter images | Bitmap display images | Vector display images |
|---|---:|---:|---:|
| Nearest, ties away from zero | 256/288 | **288/288** | **288/288** |
| Nearest, ties toward positive | 240/288 | 240/288 | 240/288 |
| Nearest, ties to even | **288/288** | 256/288 | 256/288 |

No single rule clears all paths. Selecting the rule by the **independently known native API**, not RGB/alpha/coordinate, explains every new control. The old display-phase references retain **616/616** with ties-away; ties-even would regress four of them. Bitmap and vector display outputs agree288/288. Each path also retains144/144 equivalent signed-distance/reversed-angle pairs and144/144 shifted-origin pairs, ruling out those alternatives within the captured scope.

The new controls span origins8/32; positive/negative X/Y via eight angle/distance parameterizations; half-phase magnitudes0.5,1.5,31.5,127.5,128.5,129.5 over256; perturbations±1/65536. Filter getters and source-hidden status are read back. Source-hidden shadows are diagnostic controls only; unsupported production flags remain unsupported. Decimal trace formatting is validated separately (15 significant digits, decimal half-up) while predictions retain the exact binary input distance; formatting is not treated as filter quantization.

## Held-out r78 check

Applying ties-even to r78's explicit applyFilter API, with unchanged kernel/order/composition, yields **23040/23040 unit-alpha/unit-strength samples**. All116 earlier half-phase counterexamples disappear. The production display-object phase rule stays unchanged. This does not resolve r78's non-unit gain/alpha counterexamples, and does not license substituting applyFilter for display-filter references generally.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case shadow-phase-paths \
  --output /tmp/bvn-r79/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r79/native /tmp/bvn-r79/native/native.log \
  --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 45
python3 -m tools.probes.analyze_shadow_phase_paths \
  --native evidence/importer-loud-fail/r79/native --output /tmp/bvn-r79/analysis.json
python3 -m unittest tools.tests.test_shadow_phase_paths
```

[All rules, pairs and held-out results](analysis.json), [native capture](native/native.log), [hashes](provenance.json), [acceptance](acceptance.json). This is bounded observable behavior, not an executed-instruction/ISA claim. No reference rewrite, epsilon, tolerance, per-pixel choice or production modification.

Next compare non-unit gain/alpha across the same native APIs using unblurred explicit byte ramps and both source-hidden/source-composited output. Keep property readbacks and original bytes. Only after API behavior and operation ordering are independently constrained should those rules be tested against all crossed r78 controls and old display-filter references.

`api_specific_phase_passed=true`, `production_admitted=false`. No new GPU render; older exact CPU/GPU readbacks remain regressions. Components remain historical9/54; full AS/clip-action ownership and general rendering eligibility remain open. Full roster/Web and54 components were not rerun. Draft only; no merge/deploy/Worker.
