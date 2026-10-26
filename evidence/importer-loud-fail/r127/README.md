# r127 — one shared live GPU path matches all four Jiraiya component images

Both source-derived bindings now use one parameterized diagnostic buffer helper: original texels/masks/inner transforms→live GPU cache viewport→actual FilterGroup allocation and integer Blur→destination copy→integer normal composition. Local dimensions, authored Blur axes/passes and placement origins are data. No per-component shader/math route or intermediate PNG input is used.

All original54-suite Jiraiya references at depths27/29 and ticks0/3 are **4/4 exact images,960000/960000 RGBA pixels**, with zero channel deltas. The first horizontal-blur component is revalidated through the same implementation as the second vertical-blur component. The one-frame static image scope remains explicit; this is not a new scheduler proof or a global production rerun.

A provenance test caught that the runner's self-hash exclusion was edited after the initial GPU run. The final runner was rerun, all source/readback hashes were regenerated from that actual execution, and the strict provenance test passed. Native references and pixel thresholds were not changed.

## Reproduce

```sh
python3 -m tools.probes.run_jiraiya_pair_live --godot /path/to/Godot --output /tmp/jiraiya-pair-live
python3 -m unittest tools.tests.test_jiraiya_pair_live
```

[Summary with pinned native hashes](summary.json), generated diagnostic scripts/source fixtures/full readbacks/Godot logs under `gpu/27` and `gpu/29`, [GPU provenance](gpu/provenance.json), [acceptance](acceptance.json).

Next discriminator: source-audit Yijiao455/frame607/depth29→sprite312, another one-frame vertical-Blur component. Capture authored/clear/cache boundaries with the same native harness; independently retain its exact primitive fill, inner placement and source encoding. Require the existing shared initializer/filter math to pass those boundaries before widening the live fixture. Reject unsupported masks/affine/encoding explicitly. Do not erase source fields to fit the current diagnostic domain.

`shared_live_gpu_path_verified=true`, `production_admitted=false`. The historical production54-suite remains9/54 because it was not rerun or rebound; four formerly failing pinned Jiraiya images now have exact shared diagnostic outputs. Other components, general coverage/affine and full AS/clip-action ownership remain merge blockers. Draft only; no merge/deploy/Worker.

Validation: full Python795 pass+2skip; caches26/26, fingerprint, protected, integrity/handoff/contracts green. Production runtime unchanged; full roster/Web not rerun. Fresh shared GPU4/4 above.
