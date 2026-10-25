# r92 — isolated GPU half-step candidate clears the original leaf

The independently measured r91 half-step rule now passes a real Godot Compatibility GPU diagnostic: **71824/71824** old native sampler controls, and **6/6** original r89 Jiraiya leaf images (**589824/589824 premultiplied RGBA pixels**). Native images, raw SWF bitmap273/shape274, fill matrix and directed mask are unchanged.

The isolated sampler differs from the pinned r32 sampler only by clipped half-step ties-to-even and explicit translation-only fill subtraction. Repeat initialization and geometry-only256-pixel/period/bulk partition stay unchanged; a source-delta test guards this. The old renderer is copied into a scratch project with only its coordinate-provider preload changed. Its shader remains unchanged. The leaf renderer uses the same integer interpolation shader with an explicit raw-premultiplied output mode, preserving GPU alpha rather than applying getPixel32 unpremultiplication.

The source-bound renderer checks the actual rectangular authored mask, positive axis transforms, nonrepeat/smooth fill and translation-only fill matrix. It computes bounds in double precision. It **rejects nontransparent source texels in every fractional-edge footprint**: no fractional area approximation is admitted. All six original images satisfy that restriction. This does not establish general fractional coverage, rotation, negative scale, PNG decoding or complete filtered-component semantics.

The first leaf run rejected because JSON floating-number arrays did not compare equal to integer literal arrays in GDScript. The corrected guard compares each numeric channel explicitly to zero; the failed log is retained. No texel, native image or arithmetic was changed to resolve that type-only rejection.

## Reproduce

```sh
python3 tools/probes/run_half_even_bitmap.py --godot /path/to/Godot --output /tmp/bvn-r92/recheck
python3 -m unittest tools.tests.test_half_even_bitmap_gpu tools.tests.test_clipped_half_step
```

[GPU report](gpu/report.json), [hashes/commands](gpu/provenance.json), exact readback PNGs and logs under `gpu/`, [acceptance](acceptance.json). The Python readback tests reconstruct native references and compare every image pixel again; successful console text alone is insufficient.

Next discriminator: retain this exact raw input and actual authored transform while adding Jiraiya's source BLURFILTER15×0/3 passes. Validate actual buffer bounds/quantization and complete ordinary composition against the pinned54-suite image. Do not infer a filtered-component pass from a leaf pass. Probe explicit native filter materialization if bounds or input rasterization remain ambiguous.

**`production_admitted=false`**; complete54-suite remains historical9/54 (not rerendered). Full AS/clip-action ownership, general coverage/affine, JPEG3/implicit buffer boundaries remain open. Draft only; no merge/deploy/Worker.

Fresh Python724 pass +2skip; caches26/26, fingerprint, protected, integrity, handoff/contracts green. Full roster/Web not rerun: production unchanged.
