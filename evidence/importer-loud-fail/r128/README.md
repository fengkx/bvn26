# r128 — Yijiao static component isolates source binding from already exact Blur

The unchanged generic native harness captures Yijiao455/frame607/depth29→sprite312 at three integer offsets. Original authored, clear and cache-only paired transparent/black images retain source/filter properties and public matrices. Primitive depth access has the same owner-matrix observation as the independently proven r125 case; it is not interpreted as an inner transform.

Cache and clear inputs are **720000/720000 exact**. Applying the unchanged integer vertical Blur0x10/quality1 to the measured cache reproduces authored output **720000/720000 exact**. The central authored image composed on the pinned background matches both original54-suite images: **480000/480000 exact**. Thus this bounded component needs source binding verification rather than new filter arithmetic.

## Reproduce

```sh
python3 -m tools.probes.build_component_cache_boundaries --cases evidence/importer-loud-fail/r21/components/yijiao/cases.json --case yijiao-455-607-29 --output /tmp/yijiao-boundary --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/yijiao-boundary/components/yijiao /tmp/yijiao-boundary/components/yijiao/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_component_cache_boundaries --native evidence/importer-loud-fail/r128/native --output /tmp/yijiao-boundary-analysis
python3 -m unittest tools.tests.test_yijiao_cache_boundaries
```

[Measured summary](summary.json), native capture/environment under `native/`, original boundary images under `images/`, [provenance](provenance.json), [acceptance](acceptance.json).

Next discriminator: independently extract raw bitmap310/shape311/wrapper312 fields and actual contour order, then use the same source cache initializer and integer Blur to compare all boundaries. Preserve any cyclic start vertex in stored mask metadata; prove equivalent ordered edges before accepting it rather than replacing the source mask. Reject fields/encoding/coverage outside the bounded domain. GPU binding follows only after exact CPU source images.

`source_derived_input_verified=false`, `production_admitted=false`. Historical full production54-suite9/54 unchanged; exact shared Jiraiya GPU4/4 retained. Full AS/clip-action ownership and general coverage/affine remain open. Draft only; no merge/deploy/Worker.

Validation: focused Python2/2; prior r127 full795 pass+2skip retained. Fresh caches26/26, fingerprint, protected, integrity/handoff/contracts green. Production unchanged; roster/Web and GPU not rerun.
