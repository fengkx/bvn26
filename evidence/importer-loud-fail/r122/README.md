# r122 — pinned Jiraiya component RGB images match with actual destination copy

The r121 source-derived GPU cache/filter chain is rerun, then its final composite uses the unchanged r36 integer ordinary-composition shader. An actual BackBufferCopy immediately before Composite captures the actual96/96/96 opaque background. No final PNG is synthesized from a native image.

The original54-suite `jiraiya-342-766-27` references at ticks0/3 are **2/2 exact images,480000/480000 RGBA pixels**, with all channel deltas0. The source wrapper has one frame; the diagnostic renders that same static state twice. This is image parity, not a new playhead/scheduler proof. All source cache, padded input and filter stages also rerun exact in the nested `gpu/source` evidence.

The intermediate GPU-cache PNG reload remains deliberate and explicit here; it has not been mistaken for a live texture dependency. No production binding was enabled. The full production54-suite was not rerun, so its historical9/54 count is unchanged; these two formerly failing pinned images now have exact bounded diagnostic outputs.

## Reproduce

```sh
python3 -m tools.probes.run_jiraiya_pinned_composite --godot /path/to/Godot --output /tmp/jiraiya-pinned
python3 -m unittest tools.tests.test_jiraiya_pinned_composite
```

[Summary and exact native image hashes](summary.json), images/fixtures/Godot logs and provenance under `gpu/`, [acceptance](acceptance.json).

Next discriminator: replace the explicit cache PNG reload with a live ViewportTexture from the same sampler while retaining source mask validation, actual FilterGroup allocation/order, destination copy and the exact same native image gate. Verify ownership and texture dependency while both viewports are alive. Keep global production admission false; general coverage/affine, remaining components and full AS ownership remain unproven.

`exact_images=2`, `production_admitted=false`, `full_production_suite_rerun=false`. Draft only; no merge/deploy/Worker.

Validation: focused Python2/2; prior r121 full783 pass+2skip retained. Fresh caches26/26, fingerprint, protected, integrity/handoff/contracts green. Production unchanged; roster/Web not rerun. GPU counts above.
