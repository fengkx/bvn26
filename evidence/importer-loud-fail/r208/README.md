# r208 — complete live main ColorMatrix family12/12 exact

The source-backed actual FilterGroup diagnostic improves **10/12→12/12 complete native images**, **2880000/2880000 final RGBA pixels exact**. Identity-state active images previously differed2423/530 pixels; both now have zero differences. All18 local-input/Contents/filtered comparisons are also exact, **979416/979416 RGBA pixels**. Empty-frame clocks/removal and all authored post-CXFORM states remain unchanged.

Only a diagnostic subclass overrides the matrix pass material after invoking actual production FilterGroup allocation. It asserts original input texture identity, original authored matrix, pass size, source bounds and final texture dependency. Packed coefficients derive from that source matrix under the same CPU guards. Original raw bitmap bytes, fill metadata, masks, live coverage sampler, cache allocation, post-filter transform and destination-copy composition are retained. No CPU/native-rendered image is uploaded as the component's source.

The shader uses the same include independently verified against401784 native GPU row samples in r207. The first live run correctly rejected a shader uniform-name collision; renaming the diagnostic uniforms fixed compilation, without changing arithmetic or accepting fallback pixels. The successful run contains no shader errors.

[All final and intermediate comparisons](gpu/report.json), [engine log](gpu/godot.log), [source/input/readback hashes](gpu/provenance.json), [acceptance](acceptance.json). Scratch binary textures regenerate from source and are not committed; all readback PNGs are retained.

```sh
python3 -m tools.probes.run_packed_matrix_family --godot /path/to/Godot --native evidence/importer-loud-fail/r195/native --output /tmp/matrix-packed-family
python3 -m unittest tools.tests.test_packed_matrix_family tools.tests.test_packed_matrix_rows
```

Source-backed complete live/wrapper diagnostics now cover **36 unique original images** (previous34 plus two active main identity images). This is not a fresh global production54 run: that suite remains historical9/54 and `production_admitted=false`. Production shaders/import data remain unchanged. Full AS/clip-action ownership still blocks merge.

Next discriminator: refresh the exact image-to-diagnostic coverage inventory for all54 pinned images, then source-inventory an uncovered component's complete fill/transform/cache graph before extending eligibility. Yijiao's ColorMatrix graph has smooth affine input, outer scale and blendMode5; its identity matrix is not the newly solved arithmetic blocker. Preserve those fields and compare actual unfiltered/cache boundaries before changing sampling. Keep all current matrix/sampler/leaf/filter gates exact. Draft only; no merge/deploy/Worker.
