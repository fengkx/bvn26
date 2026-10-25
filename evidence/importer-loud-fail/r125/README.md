# r125 — primitive depth lookup aliases the owner, not the authored shape transform

Independent native strict-identity/path/depth controls prove that `child.getInstanceAtDepth(1-16384)` for this original primitive shape returns **child itself**. Both paths are `/source/instance1`, both depths-16355, and strict identity is true. It is distinct from the outer `/source`; an absent depth is undefined. A separately created MovieClip at depth123 returns that distinct child, so the control does not collapse every object to its owner.

The public matrix readback consequently describes the wrapper. It does not erase the source placement: independently exported and raw-tag-hash-pinned wrapper277 places shape276 at(-17,-10)twips; the smooth clipped bitmap166 fill has(+17,+10)twips and scale20. Both matrices are retained. This is a bounded AVM1 identity observation, not a Godot node-identity implementation or a completed AS ownership audit.

## Reproduce

```sh
python3 -m tools.probes.build_component_shape_identity --output /tmp/shape-identity --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/shape-identity/components/jiraiya /tmp/shape-identity/components/jiraiya/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 60
python3 -m tools.probes.analyze_component_shape_identity --native evidence/importer-loud-fail/r125/native --output /tmp/shape-identity.json
python3 -m unittest tools.tests.test_component_shape_identity
```

[Observations and authored matrices](summary.json), original log/environment and source XML under `native/`, [provenance](provenance.json), [acceptance](acceptance.json).

Next discriminator: render the second component cache from original bitmap166 texels and shape276 mask, retaining the inner placement translation through the already independently constrained quarter-pixel composition step. Compute cache bounds in wrapper coordinates, normalize the wrapper, then compose the actual inner transform. Compare all three r124 cache boundaries before applying vertical Blur and the two pinned final images. Do not substitute the owner matrix for the shape or remove cancelling offsets from metadata.

`primitive_depth_returns_owner=true`, `primitive_readback_is_inner_transform=false`, `source_derived_input_verified=false`, `production_admitted=false`. No production changes; full AS ownership and remaining component/coverage/affine gates stay open. Draft only; no merge/deploy/Worker.

Validation: focused Python2/2; prior r124 full789 pass+2skip retained. Fresh caches26/26, fingerprint, protected, integrity/handoff/contracts green. Production unchanged; roster/Web and GPU not rerun.
