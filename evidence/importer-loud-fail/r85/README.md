# r85 — actual filter/BlendGroup boundaries and destination-copy ordering

The r84 native materialization now has a matching isolated GPU graph: actual diagnostic FilterGroup →64×64 materialized filtered viewport → production BlendGroup with child opacity in a transparent viewport → production BlendGroup with middle layer and parent opacity → transparent destination. The integer filter shader is unchanged from r81; integer ordinary composition is unchanged from r37.

Fresh destination-copy ordering is exact at all seven stages: **46080/46080 RGBA samples each** for input, middle, destination, filtered, child, parent and final. This includes non-white source, both native filter APIs, non-unit child/parent opacity, transparent through opaque destinations and fractional shadow offsets.

A deliberate stale-copy control moves the child's destination capture before the middle sibling. Input/filter/child stages stay46080/46080, while parent and final each fall to **0/46080**. The gate exits1 as intended; it cannot silently accept the wrong background snapshot. Fresh run exits0.

Both BlendGroups must be actual `res://blend_group.gd` nodes; actual Contents sizes64×64, origins, composite texture identity and viewport-source dependencies are asserted. Filter allocation and source bounds are asserted too. No production file or eligibility is changed. The explicitly allocated64×64 filtered boundary matches the native probe; this is not a claim about arbitrary implicit Flash cache allocation.

## Reproduce

```sh
python3 -m tools.probes.run_shadow_opacity_gpu --godot /path/to/Godot --output /tmp/bvn-r85/fresh
# Must exit1 and differ only after the deliberately stale destination copy:
python3 -m tools.probes.run_shadow_opacity_gpu --godot /path/to/Godot --output /tmp/bvn-r85/stale --copy-order stale
python3 -m unittest tools.tests.test_shadow_opacity_gpu
```

Full RGBA readbacks, comparisons, hashes and15 clean batch inputs/logs per order are under `fresh/` and `stale/`; comparisons are compressed JSON. [Acceptance](acceptance.json). Godot4.7.2 Compatibility, AppleM2 OpenGL4.1 Metal90.5. No tolerance, reference rewrite or RGB-selected route.

Next isolate **PNG decode and premultiplication** independently with all-alpha/color-byte controls loaded by native Flash, retaining original encoded bytes and source readbacks. Current exact GPU sources are native input bytes, so do not infer a PNG-upload rule from them or from the small102-texel Yulong case. Then test the proven decoder path separately before extending component eligibility. General fractional coverage, affine and arbitrary implicit/nested buffers remain open.

`fresh.passed=true`, `stale.passed=false`, `production_admitted=false`. Historical components9/54 not remeasured; AS/clip-action ownership remains a separate merge gate. Full roster/Web export not rerun (production unchanged). Draft only; no merge/deploy/Worker.
