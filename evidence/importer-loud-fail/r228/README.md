# r228: joint corner constraints reject universal vertical-first interpolation

Reuses pinned r227 native responses; no new capture or rendering. A single contiguous2x2 source footprint and shared 8-bit fractions must explain all four corner impulses at all three amplitudes. Nine predeclared cells touching the source corners, plus an explicit disjoint state, cover this bounded bilinear family. Exhaustive existence testing never returns a satisfying cell/fraction for rendering.

Across17640 coordinates/120unique response signatures, horizontal-then-vertical has a feasible common assignment for **17640/17640**, including **222/222** observed-active coordinates. Vertical-then-horizontal has **67 impossible coordinates**, leaving155/222active feasible. All67counterexamples, sum-response observations and family limits are retained in analysis.json.

This rejects universal VH within the declared family. HV feasibility does not prove an initializer, coordinate precision, partition rule or eligibility. No output-selected parameter is passed to a sampler; candidate/GPU/production admission remainfalse. The complete r227 and r225 counterexamples are linked by SHA and retained, not replaced by this subset.

## Reproduce

```sh
python3 -m tools.probes.analyze_jinye_joint_impulses --output /tmp/bvn-r228/analysis.json
python3 -m unittest tools.tests.test_jinye_joint_impulses
```

Four focused tests include common-footprint constraints, incomplete-coordinate rejection and an intermediate-floor witness. Mandatory gates recorded in acceptance.json/checks. Retained full Python1011pass/2skip fromr227; no production changes or fresh roster/Web/54image run. Complete diagnostic coverage46/54, historical production9/54. Full AS/clip-action ownership remains open.

## Next discriminator

Apply independently defined existing affine coordinate constructions with one fixed HV operation sequence globally against pinned ramps, all impulse amplitudes and originalr221JPEG leaves. Do not consume any locally feasible factor/cell from this round. Retain exact axis/repeat suites and all rejected affine models; HV feasibility here must not become a universal production routing claim. Only exact independently constructed coordinates plus operation order may advance.
