# r77 — actual multi-pass Glow and zero-offset Shadow nodes are exact

The540 pinned r76 native cases now run through production-created FilterGroup nodes, with diagnostic integer blur and the globally measured horizontal-then-vertical grouping. The existing production Glow/Shadow composition shader is unchanged. All original source references, intermediate texture dependencies and actual allocation sizes/origins are asserted.

| Actual GPU stage | Exact RGBA samples |
|---|---:|
| Input buffer | **69120/69120** |
| Blur buffer versus separate native Blur control | **69120/69120** |
| Glow / zero-offset DropShadow output | **69120/69120** |
| Final raw byte copy | **69120/69120** |

The diagnostic reconnects production-created blur pass nodes, then feeds the grouped result into the existing final composition node. Its `original_texture` must still reference the real unfiltered Contents texture. It never substitutes CPU-rendered filter outputs. Actual consumed operands, pass order and filter-family identities are retained in GPU readbacks and independently checked by Python.

Native Blur controls remain separate materialized operations, not claimed to expose native Glow/Shadow internals. The actual GPU blur buffer happens to match those independent controls exactly. The final stage is a `blend_disabled` byte copy, not ordinary production composition. Explicit premultiplied RGBA8 source upload remains the diagnostic input; no PNG/general affine conclusion is inferred.

## Reproduce

```sh
python3 -m tools.probes.run_grouped_family_gpu --godot /path/to/Godot \
  --output /tmp/bvn-r77/render
python3 -m unittest tools.tests.test_grouped_family_gpu
```

[Exact comparison](render/comparison.json), [actual GPU stages and operands](render/rows.json.gz), [source/native hashes and commands](render/provenance.json), [acceptance](acceptance.json). Twelve batches reuse unchanged r76 native captures; no new Flash capture. All fixtures and clean logs are retained under `render/batches/`.

Scope remains outer Glow and zero-distance DropShadow at unit alpha/strength, qualities1/2/3 and the r76 source/kernel grid. Next independently cross nonzero positive/negative fractional shadow offsets with multi-pass filtering, retaining actual offset property readbacks and earlier r20 offset controls. Non-unit filter strength/alpha also need their own measured gate. Do not globally enable from this bounded diagnostic.

`production_admitted=false`. Production source/shaders remain unchanged. Prior r74/r75 exact GPU and r71–r76 CPU controls remain pinned regressions. Older graphical suites were last re-rendered in r74; full roster/Web and54 component images were not rerun. Components remain historical9/54; AS/clip-action ownership and general production rendering eligibility remain merge blockers. Draft only; no merge/deploy/Worker.
