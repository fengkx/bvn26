# r119 — one independently measured origin clears all retained cache families

The unchanged r116 separate geometry/translation support rule, r118 common consumed-twip endpoints and r112 device-space normalization are applied to every retained cache-origin family. Original native bytes, interior selection and source fill offsets are unchanged. Geometry minima come from authored controls, never matching output RGB.

| Native suite | Exact RGB samples |
| --- | ---: |
| r101 |37842/37842|
| r102 |240900/240900|
| r103 |68544/68544|
| r104 |19980/19980|
| r109 |15048/15048|
| r113 fixed geometry |17934/17934|
| r113 moved geometry/fill |17934/17934|
| r113 moved geometry only |17934/17934|

**Total436116/436116, all channel deltas0.** This clears the old remaining12583 r102 and194 r109 counterexamples without regressing any exact family. No old initializer is spliced into selected cases. The bounded source-origin model now has independent alpha-support and cache-only RGB evidence; complete source component/GPU admission remains separate.

## Reproduce

```sh
python3 -m tools.probes.analyze_separate_cache_origins --output /tmp/separate-origins.json
python3 -m unittest tools.tests.test_separate_cache_origins
```

[Summary](summary.json), per-case results in `analysis.json.gz`, [pinned sources/native references](provenance.json), [acceptance](acceptance.json). This round reuses native readbacks; no new Flash capture or environment change.

Next discriminator: use this unchanged source-derived2D origin/normalization to render the original Jiraiya bitmap273/shape274/wrapper275 cache input at all three r100 integer offsets. Preserve original fill masks and fractional-coverage rejection, then apply the already proven integer Blur15x0/quality3 and compare original authored images. Only after full source-derived images are exact should the diagnostic GPU binding advance. General affine and nontransparent fractional coverage are not proven.

`source_cache_initializer_admitted=false`, `gpu_advance_allowed=false`, `production_admitted=false` until complete component binding gates. Historical production components9/54; AS/clip-action ownership open. Draft only; no merge/deploy/Worker.

Validation: full Python779 pass+2skip; caches26/26, fingerprint, protected, integrity/handoff/contracts green. No runtime change; roster/Web and GPU/component renders not rerun.
