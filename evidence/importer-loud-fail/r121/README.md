# r121 — complete source-derived Jiraiya GPU cache and filter buffers are exact

The original SWF texels/mask and r120 source-derived local cache transform are rendered by the unchanged admitted diagnostic GPU sampler. Its raw premultiplied PNG readback is explicitly reloaded and byte-checked, then passed through actual production-created FilterGroup buffers with the existing diagnostic integer Blur implementation. Native images never supply input pixels.

All three original integer-offset controls are exact at every boundary:

| Boundary | Exact RGBA pixels |
| --- | ---: |
| GPU local cache75x74 |16650/16650|
| Actual padded input117x74 |25974/25974|
| Actual filtered buffer117x74 |25974/25974|
| Final600x400 transparent destination |720000/720000|

Allocation assertions retain source bounds75x74, padding21x0, three horizontal passes, kernel15 and texture dependency order. Fresh old GPU sampler controls **71824/71824** and original leaf images **6/6** remain exact. No channel tolerance or native-reference rewrite.

This is a deliberately materialized diagnostic chain: GPU cache readback→PNG decode/upload→FilterGroup→raw integer placement. It does not yet prove a seamless live production texture binding, final ordinary background composition, general fractional coverage/affine or nested opacity. It does not globally change the production sampler/filter path or54-suite count.

## Reproduce

```sh
python3 -m tools.probes.run_jiraiya_source_cache_gpu --godot /path/to/Godot --output /tmp/jiraiya-source-gpu
python3 -m tools.probes.run_half_even_bitmap --godot /path/to/Godot --output /tmp/sampler-regressions
python3 -m unittest tools.tests.test_jiraiya_source_cache_gpu
```

[Summary](summary.json), GPU images/configuration/commands under `gpu/`, old strict reruns under `regressions/`, [acceptance](acceptance.json). Pinned native references remain r89/r99/r100. Environment: Godot4.7.2 Compatibility, AppleM2/OpenGL4.1 Metal90.5; exact executable/source/readback hashes in `gpu/provenance.json` and `regressions/provenance.json`.

Next discriminator: use actual destination-copy ordering and the unchanged r36 ordinary integer composition on the pinned54-suite gray background. Compare Jiraiya342/frame766/depth27 at both native ticks0/3; do not count transparent intermediate success as final RGB parity. Then test a live GPU cache texture connection before any production eligibility. Full AS/clip-action ownership remains separate.

`diagnostic_passed=true`, `production_admitted=false`. Historical production components9/54, no global enabling. Draft only; no merge/deploy/Worker.

Validation: full Python783 pass+2skip; fresh caches26/26, fingerprint, protected, integrity/handoff/contracts green. No production runtime change; full roster/Web export not rerun. Fresh GPU counts above.
