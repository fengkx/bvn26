# r130 — six pinned component images pass one live GPU path with authored masks

The GPU validator accepts only a cyclic start of the same four ordered rectangle edges. Original fixture masks remain intact; no vertex data is rewritten in the stored source binding. The existing sampler, live ViewportTexture connection, actual FilterGroup allocation/passes and integer destination-copy composition are unchanged.

Both Jiraiya components and Yijiao's static Blur component now pass **6/6 original pinned images,1440000/1440000 RGBA pixels**, zero channel deltas. The two earlier bindings rerun through exactly the same mask validator and buffer helper as the new source. No per-component arithmetic selection or PNG input boundary is introduced.

## Reproduce

```sh
python3 -m tools.probes.run_rect_components_live --godot /path/to/Godot --output /tmp/rect-components-live
python3 -m unittest tools.tests.test_rect_components_live
```

[Summary with native hashes](summary.json), generated diagnostics/source fixtures/images/logs under `gpu/`, [GPU source/readback provenance](gpu/provenance.json), [acceptance](acceptance.json).

Next discriminator: Yulong345/frame753/depth29 is a static Glow source outside the current Blur-only helper. Capture authored/clear/cache input boundaries with every native Glow property(color, alpha, strength, quality, inner, knockout) retained. Use the already independently validated common Glow arithmetic only after the original source input is explained. Then test a shared filter-family diagnostic while retaining these six exact images. Do not silently substitute Blur for Glow or enable production globally.

`shared_live_gpu_path_verified=true`, `authored_masks_preserved=true`, `production_admitted=false`. Full production54-suite remains historical9/54 (not rerun/rebound); six formerly failing pinned images have exact bounded shared diagnostic outputs. Remaining components, general affine/coverage and full AS/clip-action ownership still block merge. Draft only; no merge/deploy/Worker.

Validation: full Python803 pass+2skip; caches26/26, fingerprint, protected, integrity/handoff/contracts green. Production runtime unchanged; full roster/Web not rerun. Fresh shared GPU6/6 above.
