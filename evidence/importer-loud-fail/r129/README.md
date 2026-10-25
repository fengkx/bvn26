# r129 — source-preserved cyclic rectangle binding clears Yijiao CPU parity

A source-hash-pinned extractor preserves raw bitmap310, shape311 and wrapper312 tags, authored fill/inner matrices and the actual contour order. It rejects uncompiled wrapper actions, extra display operations, unsupported placement fields/affine/encoding and nonrectangular masks. The original contour starts at the top-right corner:80,0→80,100→0,100→0,0.

The earlier literal top-left-first guard correctly rejected this new input form. The bounded adapter now proves the same ordered rectangle edges under a cyclic start vertex, preserving the original mask in the fixture. Only its validated renderer view is normalized; no source/native reference is rewritten. Crossed edges, reversed winding, extra contours, changed boundaries and invalid extents still reject. Negative tests also exercise uncompiled actions, named inner placements and outer color transforms.

The unchanged cache initializer and integer Blur produce source cache **720000/720000**, authored Blur **720000/720000**, and both pinned final images **480000/480000** exact. No native pixels are used as rendering input.

## Reproduce

```sh
python3 -m tools.probes.extract_rect_component_leaf --cases evidence/importer-loud-fail/r21/components/yijiao/cases.json --case yijiao-455-607-29 --output /tmp/yijiao-leaf --ffdec /path/to/ffdec-cli.jar
python3 -m tools.probes.analyze_rect_component_cache --fixture /tmp/yijiao-leaf --native evidence/importer-loud-fail/r128/native --output /tmp/yijiao-source
python3 -m unittest tools.tests.test_rect_component_cache
```

[Summary retaining authored contour](summary.json), original extracted metadata/bytes in `fixture/`, six derived images in `images/`, [provenance](provenance.json), [acceptance](acceptance.json).

Next discriminator: port only the cyclic-edge validation into the shared live GPU diagnostic, keeping actual source mask metadata intact. Require Yijiao's two pinned images and all four Jiraiya images to pass the same sampler/filter/composition helper. Do not enable production globally or admit arbitrary polygon coverage.

`source_derived_cpu_component_exact=true`, `gpu_binding_verified=false`, `production_admitted=false`. Production54-suite historical9/54 not rerun; general affine/coverage and full AS ownership remain open. Draft only; no merge/deploy/Worker.

Validation: focused Python4/4 including negative guards; prior r127 full795 pass+2skip retained. Fresh caches26/26, fingerprint, protected, integrity/handoff/contracts green. Production unchanged; roster/Web and GPU not rerun.
