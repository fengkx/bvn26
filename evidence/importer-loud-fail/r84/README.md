# r84 — explicit filtered bytes across two opacity boundaries

360 fresh native cases explicitly allocate source, filtered result, opacity-scaled child, parent with middle layer, and final destination. Filter creation remains API-specific (applyFilter or actual bitmap display) before materializing its output in a64×64 BitmapData. Subsequent child/parent draws are separate operations; no cacheAsBitmap materialization inference.

The unchanged r37 integer bitmap-opacity/normal-over model clears all stages:

| Readback | Exact RGBA samples |
|---|---:|
| Source, middle, destination inputs | 46080/46080 each |
| Filtered bytes versus pinned r82 | 46080/46080 |
| Child after child opacity | 46080/46080 |
| Parent after middle + child | 46080/46080 |
| Final after parent opacity over destination | 46080/46080 |

Child opacity1/25/50/99/100 and parent25/50/100 vary independently; destination alpha0/1/64/128/254/255. Two source/filter configurations retain r82's non-white ramp/constant, kernels3.99609375/8.25, quality3/1, non-unit gain/filter alpha and oblique/half-phase offsets. Filter getters and every source/intermediate readback are retained.

The model consumes opacity as `floor(percent*256/100)` then floors each premultiplied byte product/256 at each explicit boundary. Source-over remains `front + floor(back*(256-front_alpha)/256)`. A negative control collapsing the opacity boundaries matches only **38254/46080**, rejecting7826 samples. This prevents replacing materialized layers with multiplied scalar opacity.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case shadow-materialized-opacity --output /tmp/bvn-r84/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r84/native /tmp/bvn-r84/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 45
python3 -m tools.probes.analyze_shadow_materialized_opacity --native evidence/importer-loud-fail/r84/native --output /tmp/bvn-r84/recheck.json
python3 -m unittest tools.tests.test_shadow_materialized_opacity
```

[Comparisons](analysis.json), [capture](native/native.log), [hashes](provenance.json), [acceptance](acceptance.json). The four filtered references are selected by exact authored source/filter/API identity from r82, not by their output RGB; all original input bytes must also match.

Next bind these explicit boundaries to actual GPU filter and BlendGroup nodes with a fresh destination copy at each composition; retain intermediate texture readbacks and add a stale-copy negative control. Require exact native outputs before broader eligibility. Raw PNG decoding, fractional coverage, affine and general nested scene behavior remain outside this proof.

`passed=true`, `production_admitted=false`. No production/GPU changes this round. Components historical9/54 and AS/clip-action ownership remain open. Full roster/Web and54 component images not rerun. Draft only; no merge/deploy/Worker.
