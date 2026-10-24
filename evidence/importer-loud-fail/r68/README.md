# r68 — conservative ceil extent rejected by fractional kernels

The globally defined candidate pads by `ceil((kernel+1)/2)` on each side and includes the far endpoint, giving width `source_width+2*padding+1`. Its geometry depends only on source bounds/kernel, not RGB. The same scalar/long arithmetic remains unchanged.

This candidate matches **46,720/46,720** old integer-kernel implicit pixels (r62+r66), but new native controls reject it:

| New240-case gate | Exact pixels |
|---|---:|
| Implicit vs explicit filtered bytes | 38400/38400 |
| Declared explicit extent arithmetic | 38400/38400 |
| Implicit vs conservative explicit final | **38218/38400** |

The182 failures occur only at requested/retained kernels3.5,3.99609375,7.5,7.99609375. Values4,4.00390625,4.5,8,8.00390625,8.5 are retained controls; widths5,9,13,17,33,64, origins40/41 and opacities100/50 vary independently. Each case emits retained blurX, public rectangle, actual explicit width/height and translation. Paired transparent/black reads preserve pre-transform and final bytes.

The candidate is rejected globally, despite clearing every prior integer control. No fractional-kernel correction, formula splice, tolerance or per-case padding is introduced. `conservative_model_admitted=false`, `production_admitted=false`; analysis exits1.

## Reproduction

```sh
python3 tools/probes/build_flash_filter_probe.py --case filter-conservative-extent \
  --output /tmp/bvn-r68/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r68/native /tmp/bvn-r68/native/native.log \
  --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 45
python3 -m tools.probes.analyze_conservative_filter_extent \
  --native evidence/importer-loud-fail/r68/native --output /tmp/bvn-r68/analysis
python3 -m unittest tools.tests.test_conservative_filter_extent
```

[All sites](analysis.json), [provenance](provenance.json), [native capture](native/native.log), [acceptance](acceptance.json). Old references are unchanged. No new GPU render, production shader/runtime change or merge-readiness claim.

Next distinguish consumption of the fractional kernel for internal extent construction from the independently measured public rectangle API. Use a single globally defined integer-consumption construction and reject it against all old/new controls before any GPU change; preserve separate before/after-transition values and retained property readbacks. Matching a selected border or image remains insufficient evidence of actual internal allocation.

Components remain historical9/54; AS/clip-action ownership and other visual gaps remain open. Full roster/Web export and unchanged graphical suites were not rerun; pinned exact regressions remain in Python. Draft only; no merge/deploy/Worker.
