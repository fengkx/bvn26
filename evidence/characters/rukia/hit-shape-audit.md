# Base hit-shape audit

## Source identity and method

The offline JPEXS 26.2.1 XML exports were produced from the locked SWFs with `-swf2xml` (no import or source modification). Exported source SHA256 values were checked against the files in `game/fighter/` before reading geometry:

| Source | SHA256 | XML export SHA256 |
|---|---|---|
| `game/fighter/rukia.swf` | `c48d47a817dbf1b4fff9b333bb35d89debb64d0635e8d88b4a7d1228208194eb` | `0f049965384334059f854155e3d4e6328fb682988df1e47d13090fbba8661055` |
| `game/fighter/yihu.swf` | `9f089bd3ee428382d8b99543a7534fb0f271ede09ed264b74847ca7cffcf1ac8` | `595162cd13d4cf31500753073d0d99554e96915386a0434ed5e961b73edbf8b3` |

The export working files are in `/private/tmp/rukia-shape-audit/`; they are disposable tool output, not source assets.

## Shape and instance mapping

Rukia's base fighter timeline is `DefineSprite 533`. Its frame 222 places the named `k1atm` instance at depth 28 using character id 2. In Yihu's base fighter timeline, `DefineSprite 638`, named `bdmn` is also a placement of character id 2. In both locked SWFs, character id 2 is a one-frame `DefineSprite` that places character id 1 at depth 1 with an identity matrix. Character id 1 is `DefineShape3`.

The two `DefineShape3` records are identical geometrically:

- RECT: `Xmin=0, Ymin=0, Xmax=1319, Ymax=810` twips (65.95 × 40.5 source pixels).
- The filled path starts at `(1319,810)` and follows edges `(-1319,0)`, `(0,-810)`, `(1319,0)`, `(0,810)`, closing at its start. Its geometric extrema equal the RECT extrema exactly.
- One solid RGBA fill is present with alpha `0`; there are zero line styles and no stroke width to add to the bounds.
- The hit clip's child placement has identity transform. The actor timeline's placement matrix is applied outside this shape.

Thus, for these Rukia attack and Yihu hurt clips, a path-vs-RECT geometry difference cannot explain the remaining transformed-bound differences: the source path and source RECT have identical extrema, and there is no stroke. This does not identify Flash Player's internal transform/quantization algorithm for `MovieClip.hitTest`.

## What the Godot bounds path reads

`tools/importer/extract_timeline_geometry.py` exports `shape_bounds_twips` from each shape's SWF `shapeBounds` RECT; it does not preserve the source edge-record path in the runtime JSON. `TimelinePreview._definition_bounds()` reads those twips and converts them to source pixels, while `_placement_bounds()` applies each display-list placement matrix. Fighter contact queries then pass the resulting rectangles to `SourceHitTest.intersects()`, which uses inclusive `Rect2.intersects(..., true)` after rejecting empty rectangles. In this particular source pair, using the RECT as the shape bound is supported by the exact path/RECT equality above. The remaining mismatch is in bound/coordinate quantization, not path shape or stroke expansion.

## R07 evidence scope correction

The original `rukia-hierarchy-r02` log SHA256 is `bb06949d36553e2538b4c33ea6ba3af8004404d321891709960e11115b09e536`. At display tick 487 / fight tick 14, the original `bdmn.hitTest(k1atm)` result is `true`; attack `getBounds(game).yMax` is encoded as `f:-1:4:123941683:13421773`, which decodes to `-29.55`.

The controlled run `rukia-controlled-hit-geometry-r05` log SHA256 is `dc98a459cdd82dc5bbae294b6854d08b29703aa8c8cffcbe530ecfe7bc9aafe9`. Its event has the same encoded attack `yMax=-29.55`; the other three game-space endpoints and all four root-space endpoints also match the original capture. The gate checks both clips' local bounds, all four public bounds rectangles, instance paths and parent links, frames, matrices, game/root transforms, and actor transforms. The event label `r07_exact` overstates what was done because the actors and frames were manually set in a controlled intervention. The corrected classification for this evidence is `structure_matrix_match`; it is not a full replay of the original input tape. A single-decimal summary `-29.6` was rounded display text, not the value recorded in the source log.

## Offline matrix-rounding candidate

A separate, explicitly non-authoritative comparison applied the candidate described by Ruffle's `Matrix` implementation: use f32 linear coefficients, compose each ancestor as `parent * child`, round the transformed child translation to integer twips using ties-to-even at each multiplication, then apply the accumulated matrix to each source-RECT corner with the same twip rounding. The implementation describes this as Flash-compatible, but it is still a third-party emulator candidate and is not Flash Player evidence. See [Ruffle matrix arithmetic](https://github.com/ruffle-rs/ruffle/blob/master/render/src/matrix.rs#L170-L226) and [its stated rounding rule](https://github.com/ruffle-rs/ruffle/blob/master/render/src/matrix.rs#L275-L289). Ruffle's current `world_bounds` accumulates matrices before transforming leaf bounds, and object `hitTest` compares the two world bounds; its `getBounds(target)` instead transforms bounds through the target inverse, which is why these APIs need separate comparison. See [world bounds](https://github.com/ruffle-rs/ruffle/blob/master/core/src/display_object.rs#L1284-L1333), [object hit test](https://github.com/ruffle-rs/ruffle/blob/master/core/src/display_object.rs#L2442-L2454), and [AVM1 getBounds](https://github.com/ruffle-rs/ruffle/blob/master/core/src/avm1/globals/movie_clip.rs#L1355-L1414).

Using the captured local matrices and the verified source RECT `[0,0,1319,810]` twips, the candidate starts at the leaf and walks outward. At each step it computes `new = parent * accumulated_child`; each scalar multiply/add is rounded to f32, and the transformed child translation is rounded to an integer twip with ties-to-even before the parent translation is added. Reversing the traversal or changing the association order changes a receiver endpoint by one twip. This rule predicts all four captured `_root` boxes exactly:

| Capture and clip | Predicted root bounds (twips) | Observed root bounds (twips) |
|---|---:|---:|
| Rukia tick 14 receiver | `[6452,5342,7467,7046]` | `[6452,5342,7467,7046]` |
| Rukia tick 14 attack | `[4722,6485,6452,6873]` | `[4722,6485,6452,6873]` |
| R13 sensor | `[11196,293,15457,7381]` | `[11196,293,15457,7381]` |
| R13 target | `[15458,5766,16286,7308]` | `[15458,5766,16286,7308]` |

Those predicted root rectangles touch for the Rukia pair, matching its `true` result, and leave a one-twip horizontal gap for the R13 pair, matching its `false` result. The reversed `child * parent` order produces boxes far from both captures and is rejected.

The same candidate does **not** reproduce every public `getBounds(game)` endpoint: Rukia receiver `yMax` is predicted `-501` twips versus observed `-500`; R13 sensor `xMax/yMax` are predicted `(16528,-419)` versus observed `(16527,-420)`. The Rukia attack and R13 target game-space bounds match. These observations keep public `getBounds(game)` separate from global `hitTest` bounds.

## Collision-only implementation and replay

`SourceMatrixBounds` now computes source global collision rectangles directly from the source RECT and each local SWF matrix, preserving integer twips through composition and applying the leaf-up f32/ties-even rule above. `TimelinePreview.instance_global_bounds()`, `named_instances_global_bounds()`, and `child_instance_global_bounds()` use this path; `AiSenses.global_bounds()` and helper contact bounds use it as well. Local bounds, body-width reads, ledge checks, and rendering transforms retain their previous calculation because the available evidence does not show that public `getBounds(target)` shares the hit-test path.

The original Rukia neutral 砍1 fixture was replayed without changing its input window or source capture. All 602 source/native state rows and all 14 compared fields match exactly; at fight tick 15 the attack reaches the original tangency and the following source state records the expected hit (`P2 frame 739`, HP `970`, energy `303`, hits `1`). The saved replay and comparison are in [collision-matrix-implementation-r01.json](collision-matrix-implementation-r01.json) and [native.json](collision-matrix-implementation-r01/native.json). Existing r13 and r14 tapes also retain their prior observed-field results after the global bounds change: 897/867 frame comparisons, 1,794/1,734 state comparisons, and complete random and clock tapes. Their reports are summarized in the same evidence record.

The production result is currently exposed as `Rect2` after the integer-twip computation, then passed through the existing inclusive `SourceHitTest.intersects()` call. The original one-twip-gap/edge contact smoke and the Rukia same-input replay pass through that production API, so this change did not add a tolerance or alter the comparator. Rotation, nested helper/projectile paths, and other camera configurations still need direct native bounds evidence before extending the claim to those cases.

## Existing mirrored and boundary observations

The short captures `rukia-geometry-r07` through `r10` record the original `hitTest` result plus public game/root bounds, but they do not contain the per-ancestor local matrices needed to independently run the matrix-rounding candidate. Their root-space observations are still useful constraints; they are not candidate validations:

| Run | Situation at fight tick 14 | Attack root X interval | Receiver root X interval | Source `hitTest` |
|---|---|---:|---:|---|
| r07 | right-facing touch | `[236.10,322.60]` px | `[322.60,373.35]` px | true |
| r08 | mirrored touch | `[277.45,363.95]` px | `[226.70,277.45]` px | true |
| r09 | 0.10 px gap | `[236.05,322.55]` px | `[322.65,373.40]` px | false |
| r10 | 0.05 px overlap | `[236.15,322.65]` px | `[322.60,373.35]` px | true |

These values are source observations from the captures. Each original run was replayed in Godot with its unchanged 300-frame input, initial positions, and attack window. All four replays matched 602/602 states across all 14 fields with no differences; this includes the mirrored true contact, r09 miss at 0.10 px separation, and r10 true contact at 0.05 px overlap. The full native traces, source logs, build metadata, and strict comparison results are retained under [collision-matrix-implementation-r01](collision-matrix-implementation-r01.json). The candidate is therefore validated against the recorded hit-test outcomes for these four cases, though the original r07–r10 logs still do not expose every local matrix needed for an independent offline reconstruction of each chain.

Raw capture logs and SHA256: r07 `/private/tmp/rukia-geometry-r07-capture/original.log` `d1cbb9f35c21f4afe9a149f39a92054ffd7acbca5422c619422fdd76f2173a3b`; r08 `/private/tmp/rukia-geometry-r08-capture/original.log` `2671f41b080b4e0ece154ae79e0fd4561779ecbbcfb843d89125751cec9d6754`; r09 `/private/tmp/rukia-geometry-r09-capture/original.log` `484aa455b7335f509ab5080f9c193aa3824b2bdd8fe55392427c0875fd6ee6a5`; r10 `/private/tmp/rukia-geometry-r10-capture/original.log` `89409eb5925daee16193130140b1554acaee734dddd16e38c80ecfbd7a1d81b7`.
