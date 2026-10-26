# r123 — live GPU texture binding retains pinned component parity

The same unchanged sampler now passes its live ViewportTexture directly into actual FilterGroup nodes. No PNG decode/readback supplies the filter input. The diagnostic asserts live texture identity,75x74 source bounds,117x74 padded buffers, three horizontal kernel15 dependencies, and destination-copy ordering before ordinary integer composition.

The original54-suite Jiraiya342/frame766/depth27 images remain **2/2 exact,480000/480000 RGBA pixels**. Both static sample references are unchanged. PNGs are output evidence only; the generated leaf diagnostic inserts a single live-stage call before the original viewport is freed. The generator asserts its exact insertion site and records the generated script hash, preserving the existing sampler and coverage rejection.

This closes the deliberate intermediate-PNG limitation of r121/r122 for this bounded component. It does not enable production globally or establish all54 images, general affine/coverage, nested opacity or AS ownership.

## Reproduce

```sh
python3 -m tools.probes.run_jiraiya_live_cache --godot /path/to/Godot --output /tmp/jiraiya-live
python3 -m unittest tools.tests.test_jiraiya_live_cache
```

[Summary](summary.json), source-derived fixture/generated diagnostic/images/logs/provenance under `gpu/`, [acceptance](acceptance.json).

Next discriminator: apply the common rules to Jiraiya's other pinned component,342/frame766/depth29→wrapper277→shape276/bitmap166. It has a translated inner shape and vertical Blur, so independently capture original authored/clear/cache boundaries and actual nested matrices before combining translations. Preserve the authored fill offset and mask; do not erase an inner transform because the ideal geometric offsets cancel. Require exact boundaries and both pinned images before widening eligibility.

`live_viewport_texture_verified=true`, `production_admitted=false`; historical production suite9/54 unchanged (not rerun). Full AS/clip-action ownership remains a separate merge gate. Draft only; no merge/deploy/Worker.

Validation: focused Python2/2; prior r121 full783 pass+2skip retained. Fresh caches26/26, fingerprint, protected, integrity/handoff/contracts green. Production unchanged; roster/Web not rerun. Live GPU counts above.
