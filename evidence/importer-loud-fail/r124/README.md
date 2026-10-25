# r124 — second Jiraiya component has the same measurable cache/filter boundary

Fresh native captures retain original wrapper277/shape276/bitmap166 at three integer draw offsets. Authored, filters-cleared/cache-off and cache-only outputs preserve full paired transparent/black readbacks, filter properties and public matrices/local bounds. No source/runtime assets were changed.

Cache-only differs from clear input at58/112/173 pixels respectively, max channel delta1. Applying the unchanged integer vertical Blur0x15/quality1 to the independently measured cache input matches **720000/720000 authored pixels**. Normal composition of the central authored capture onto the pinned gray background matches both original54-suite depth29 references: **480000/480000 pixels**. These establish native boundaries, not source-derived or GPU parity for this second component.

The attempted depth1 shape matrix readback equals the enclosing wrapper matrix in all three captures. That does **not** prove the authored shape placement has no transform: the locked shape276 placement carries translation(-17,-10)twips and its fill has(+17,+10)twips. AVM1 depth lookup may expose the enclosing script object for a primitive shape. Object identity/access semantics must be independently measured before treating this readback as an inner transform. Original readbacks are retained unchanged.

## Reproduce

```sh
python3 -m tools.probes.build_component_cache_boundaries --cases evidence/importer-loud-fail/r21/components/jiraiya/cases.json --case jiraiya-342-766-29 --output /tmp/component-boundaries --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/component-boundaries/components/jiraiya /tmp/component-boundaries/components/jiraiya/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_component_cache_boundaries --native evidence/importer-loud-fail/r124/native --output /tmp/component-boundary-analysis
python3 -m unittest tools.tests.test_component_cache_boundaries
```

[Summary with all measured channel deltas](summary.json), original native log and environment under `native/`, derived boundary images under `images/`, [provenance](provenance.json), [acceptance](acceptance.json).

Next discriminator: explicitly read strict identity, target path and depth for the primitive depth lookup versus its owner. Independently retain the authored inner placement/fill matrix from the locked SWF. Only then test the common source-derived initializer with the full transform chain against this new cache input; do not cancel the offsets by assumption or substitute the parent's matrix for the shape matrix.

`source_derived_input_verified=false`, `production_admitted=false`. First Jiraiya component has exact live GPU diagnostics; historical production54-suite remains9/54, not rerun. AS/clip-action ownership remains separate. Draft only; no merge/deploy/Worker.

Validation: full Python789 pass+2skip; caches26/26, fingerprint, protected, integrity/handoff/contracts green. No production runtime change; full roster/Web and fresh GPU not rerun.
