# r83 — non-white native inputs through the unchanged integer GPU filter

The r81 diagnostic integer shader and actual filter-buffer machinery are unchanged. A bounded source fixture uploads the native **input** row from r82 on the y24..40 rectangle authored by that probe; the independent native center-column readback is required to match this reconstruction. No filtered output is used to synthesize source pixels. Raw RGBA8 upload bytes and texture identity are asserted.

All1152 API-specific cases pass:

| Stage | Exact RGBA samples |
|---|---:|
| Actual contents buffer | 147456/147456 |
| Grouped blur buffer, including RGB | 147456/147456 |
| Integer shadow composition | 147456/147456 |
| Raw final copy | 147456/147456 |

Each native case is rendered separately with source-authored applyFilter/display identity. Their566 differing native samples remain different and are correctly reproduced. Allocation/padding, shader operands and source/final texture linkage use the strict r81 checks. There is no tolerance, reference rewrite, channel-dependent formula or production change.

This deliberately proves raw-byte filter/source composition, **not PNG decoding**. The source geometry comes from the authored probe; arbitrary masks, fractional coverage and affine transforms remain outside this fixture. The final target uses a raw copy, so transparent-destination ordinary composition needs a separate boundary test.

## Reproduce

```sh
python3 -m tools.probes.run_colored_shadow_gpu --godot /path/to/Godot --output /tmp/bvn-r83/gpu
python3 -m unittest tools.tests.test_colored_shadow_gpu tools.tests.test_integer_shadow_gpu tools.tests.test_shadow_colored_paths
```

[Comparison](render/comparison.json), [source/native/GPU hashes](render/provenance.json), [acceptance](acceptance.json). All24 clean batch inputs/logs and compressed complete GPU readbacks are retained. Godot4.7.2 Compatibility, AppleM2 OpenGL4.1 Metal90.5. Old exact gates stay strict.

Next explicitly materialize these colored filtered outputs in native Flash, then apply independently varied child/parent opacity over transparent destinations and retain every intermediate buffer. Compare the already-constrained integer composition model before binding actual production destination-copy ordering; do not infer cache materialization from cacheAsBitmap or substitute raw copy for ordinary composition.

`passed=true`, `production_admitted=false`. Components historical9/54; full AS/clip-action ownership and general PNG/coverage/affine/nested composition remain open. Full roster/Web export and54 component images not rerun because production is unchanged. Draft only; no merge/deploy/Worker.
