# Importer safety net: accepted scope and known gaps

## Merge decision (2026-10-26)

The user approved shipping PR48's wired importer/compiler/build hard-fail checks first. Exact Flash fidelity remains the target, but complete component-image parity, general sampler admission, production54 and full AS/clip-action ownership are follow-ups, not blockers for this merge. Human/Cursor review is required before merge. This decision does not authorize deployment or merging by the agent.

The safety net rejects unsupported recognized call/argument forms, non-finite values, unsupported placement fields, missing or changed source-pinned cached calls, placements and nested controls. It is **not** a claim that every possible AS statement already has a proven consumer. Full ownership audit remains incomplete and must retain its nonzero exit and inventories; no list is emptied to pass this merge.

## Rendering differences retained

`production_admitted=false`. Complete source-bound diagnostic inventory is **46/54**; Jinye4 and Yijiao4 remain unadmitted. The separate production component suite remains historically **9/54**, not newly remeasured or equivalent to the diagnostic inventory.

Frozen r249 display-matrix arithmetic was tested on actual source-decoded Jinye images in [r250](../evidence/importer-loud-fail/r250/README.md), without changing native references, coverage, cache bounds, inverse phase or composition:

| Jinye image | Differing pixels before → after | Maximum channel delta after |
| --- | ---: | ---: |
| Shape56 uncached | 17 → 0 | 0 |
| Shape56 cached | 17 → 7 | 1 |
| Shape57 uncached | 2 → 3 | 1 |
| Shape57 cached | 19 → 20 | 1 |
| Complete stage tick0 | 129 → 76 | 71 |
| Complete stage tick10 | 270 → 11 | 62 |
| Complete stage tick23 | 212 → 26 | 57 |

Only the empty complete tick20 image is exact: complete images remain 1/4, active images 0/3. The two leaf regressions remain explicit. These results do not increment the 46/54 inventory or admit the candidate. The nearest-sampling controls retain 81 cached counterexamples out of 218000; uncached controls are 218000/218000 exact. See [r249](../evidence/importer-loud-fail/r249/README.md) for the fixed construction and remaining bounds.

Yijiao's source-bound ColorMatrix, outer scale and blendMode5 complete-wrapper proof is still pending. General coverage/affine behavior, nested production composition and full sampler binding remain bounded by their existing evidence, not extrapolated from individual exact probes. No tolerance, reference replacement, per-pixel route or new allowlist was introduced to accept these differences.

## Runtime risk: the flag is not a kill switch

`FighterRuntime` inherits `TimelinePreview`; authored filters can already instantiate `FilterGroup`, alongside `BlendGroup`, in gameplay. `production_admitted=false` records incomplete evidence; it does **not** disable those nodes. PR48 includes runtime/filter/form changes relative to master, even though recent evidence rounds only modified diagnostics. Visual differences can therefore remain visible in gameplay. A runtime admission policy or complete production-path proof remains an explicit follow-up risk accepted under the revised merge bar.

## AS and clip actions

Selected call/cache gates pass for 26 shipped fighters, but the frame-call audit still inventories 1438 broader candidate sites requiring scope/consumer review. Structural clip-action validation preserves and checks serialized metadata; it does not establish the semantic owner of every event body. Arbitrary calls outside the recognized grammar and complete first-frame/nested ownership remain open. The complete `audit_importer.py` audit must continue reporting these obligations, rather than presenting selected build checks as universal coverage.

The final focused audit closes two concrete holes: explicit `this.stop/play/goto` can no longer evade nested DoAction requirements; source-pinned first root-wrapper blendMode obligations cannot disappear or change in cached metadata, including whole-wrapper deletion. Selected matching wrapper placements also compare blendMode; later root MOVE/replacement ownership is not universally established by this check. Existing exact hash-scoped exceptions remain reviewable; no new exception was added.

See [review map](PR48_REVIEW.md) for product/runtime diff commands and [merge acceptance](../evidence/importer-loud-fail/merge-review/README.md) for current checks.
