# r66 — held-out kernels reject a universal right-border rule

252 fresh native cases use widths5,8,9,12,13,21,25,35,65; origins40/41; opacity100/50; kernels2,3,4,6,7,8,9. Every case captures source input, implicit filtered/final and explicit filtered/final rows with paired transparent/black readbacks. The explicit branch always adds exactly one transparent right column, independent of output RGB.

- Implicit vs explicit **filtered bytes:40320/40320 exact**.
- Declared explicit dimensions plus unchanged admitted arithmetic: **40320/40320 final pixels exact**.
- Implicit vs explicit final: **40236/40320**;84 pixels differ, at kernels4 and8.

The fixed right-border hypothesis is therefore **rejected globally**, despite matching every r65 kernel5 control. No extra per-kernel padding, minimum width or formula splice is introduced. The native rows retain the small-width failures as well as the isolated right-edge failures; [analysis.json](analysis.json) lists exact case parameters and RGBA values.

## Independently observed rectangle behavior

| Requested kernel size | Measured symmetric generateFilterRect padding |
|---|---:|
| 2,3,4 | 2 |
| 6,7,8 | 4 |
| 9 | 5 |

Earlier odd-kernel captures could not distinguish rounding constructions. These new even-kernel measurements constrain the public rectangle API independently of the final RGB comparison. They do not yet explain internal cache allocation, nor justify choosing a rounding rule from the matched pixels.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case filter-border-heldout \
  --output /tmp/bvn-r66/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r66/native /tmp/bvn-r66/native/native.log \
  --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 45
python3 -m tools.probes.analyze_filter_border_heldout \
  --native evidence/importer-loud-fail/r66/native --output /tmp/bvn-r66/analysis
# Expected exit1. Fixed implicit-cache border hypothesis fails.
python3 -m unittest tools.tests.test_filter_border_heldout
```

[Provenance](provenance.json), [capture](native/native.log), [acceptance](acceptance.json). New native capture only; no new GPU render, production code change, tolerance, allowlist or reference rewrite. Prior exact arithmetic/readback regressions remain unchanged.

Next independently sweep filter-property values around the even-kernel rectangle transitions, reading back the retained property and actual public rectangle. Separate public rounding from implicit-cache padding before considering any new common construction. Keep the failed right-border control and all old bounds as rejection constraints, not coefficient/route sources.

Production remains disabled; components historical9/54, AS/clip-action ownership and other visual gates remain open. Full roster/Web export and unchanged graphical suites were not rerun. Draft only; no merge/deploy/Worker.
