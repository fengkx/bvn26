# r61 — independently measured filter extent clears color-order diagnostic

The pinned filter/CXFORM order diagnostic improves **2/4 → 4/4 groups**, **2558/2560 → 2560/2560 RGBA channels**. The production renderer is unchanged and remains2/4; this result is diagnostic-only. ColorMatrix/color/component counts are not raised.

## Independent geometry evidence

Fresh native Flash `BitmapData.generateFilterRect` observations cover64 combinations: source widths1,2,3,15,16,17,34,64; Blur/Glow sizes1,3,5,7; one pass. All report symmetric padding `(blur+1)/2`. In particular, a64×64 rectangle at(40,40) with5×5 Glow reports **(37,37,70,70)**. Current production allocation uses(38,38,68,68).

The r60-admitted arithmetic alone, using the current production extent, leaves two native differences at x105: red8 vs9 at opacity100 and green11 vs12 at opacity50. These are retained in `unpadded-order.json`. They are not new reciprocal counterexamples: using the independently measured logical extent changes this right-end position from the long prefix to the scalar tail under the unchanged width/prefix rule.

The new diagnostic inherits the original source scene and actual FilterGroup nodes. It keeps authored filters, fill bytes, transforms, opacity, original pinned native rows and the admitted scalar/long arithmetic. Its logical span metadata comes from the native rectangle capture and the actual group source bounds/padding. No output RGB is used to choose a route or coefficient. It does not resize production buffers or claim that public `generateFilterRect` alone proves all internal cache allocations.

## Evidence and reproduction

```sh
python3 tools/probes/build_flash_filter_probe.py --case filter-cache-bounds \
  --output /tmp/bvn-r61/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r61/native /tmp/bvn-r61/native/native.log \
  --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 25
python3 -m tools.probes.run_native_color_order --godot /path/to/Godot \
  --native evidence/importer-loud-fail/r61/native --output /tmp/bvn-r61/final
python3 -m unittest tools.tests.test_native_color_order
```

[Native observations](native/native.log), [capture environment](native/capture-environment.json), [strict comparison](render/comparison.json), [provenance](render/provenance.json), [acceptance](acceptance.json). Missing/duplicate native controls, changed source bounds, unsupported filter types, engine errors or any RGBA delta reject. No tolerance, allowlist or native-reference rewriting.

## Remaining scope

`production_admitted=false`. Next independently exercise actual filter allocation with source widths/positions that put both ends across long-prefix/tail boundaries, then compare full intermediate buffers and final images. A diagnostic logical-span correction is not a production buffer-allocation implementation. Retain r58 CPU, r59 actual nested filters72576 and r60 GPU controls1302912 as strict regressions; those code paths are unchanged and pinned by the Python tests.

The54 component images remain historical9/54; no component count improvement is claimed. Other color/ColorMatrix/rush differences and full AS/clip-action ownership remain open. Full roster/Web export was not rerun because production runtime is unchanged. Draft only; no merge/deploy/Worker.
