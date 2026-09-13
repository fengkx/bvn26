# Rukia base hitbox bounds by transform layer

## Capture

- Run: `rukia-hierarchy-r02`, fixture `rukia-218-nornalhit-neutral`.
- Input: P1 Rukia x=300, P2 Ichigo x=350, attack held on fight ticks `[10,13)`; 300 fight frames; capture completed.
- Locked source hashes: Rukia SWF `c48d47a817dbf1b4fff9b333bb35d89debb64d0635e8d88b4a7d1228208194eb`; Ichigo SWF `9f089bd3ee428382d8b99543a7534fb0f271ede09ed264b74847ca7cffcf1ac8`.
- Flash evidence: `/private/tmp/rukia-hierarchy-r02-capture/original.log` (`rukia_hier_bounds` and `rukia_receiver_test`); parsed receiver summary is `/private/tmp/rukia-hierarchy-r02-capture/summary.json`.
- The probe evaluates the original receiver `hitTest` once and reuses its result. Bounds and matrices are logged afterward. Diagnostic logging can affect wall-clock timing; original event timestamps remain in the log. No clock-tape reads were captured in this hit path.

## Source shape and first transform

The selected local shape definition has RECT bounds `[Xmin=0, Ymin=0, Xmax=1319, Ymax=810]` twips, or `[0,0,65.95,40.5]` pixels. Rukia's `k1atm` placement is present in `data/slices/rukia-base.timeline.json` frames 221–222 at depth 28, matrix scale `(0.68836975, 0.25126648)`, translation `(-335,179)` twips. Yihu's base root is Sprite 638; its `bdmn` is at depth 29 in `data/slices/yihu-base.timeline.json` frames 1–2, matrix scale `(0.40379333,1.104065)`, translation `(-315,-416)` twips.

The live local matrices resolve to 16.16 fixed-point values. Transforming the source RECT corners into the immediate parent (`mc`) gives:

| Instance | Scale numerator / 65536 | Translation (twips) | Raw transformed max (twips) | Outward twip bounds | Captured `getBounds(mc)` |
| --- | --- | --- | --- | --- | --- |
| `bdmn` | `(26463,72356)` | `(-315,-416)` | `(217.6034088,478.2926025)` | `[-315,-416,218,479]` | `[-15.75,-20.8,10.9,23.95]` px |
| `k1atm` | `(45113,16467)` | `(-335,179)` | `(572.9597015,382.5258484)` | `[-335,179,573,383]` | `[-16.75,8.95,28.65,19.15]` px |

“Outward twip bounds” here floors each transformed minimum and ceils each maximum to an integer twip. For this source RECT and these two scale-only placements, that reproduces all four observed parent-space endpoints exactly. The first fractional-twip endpoint appears at this symbol-local-to-`mc` transform.

## Transform chain at the contact tick

The probe's tick 14 is Yihu `bdmn` frame 1 and Rukia `k1atm` frame 1. Each following stage was recomputed from the previous captured AABB using that target object's local `transform.matrix` and compared with `getBounds` at the next ancestor.

| Chain | Receiver `bdmn` | Attack `k1atm` | Result |
| --- | --- | --- | --- |
| Shape → immediate `mc` | `[-15.75,-20.8,10.9,23.95]` | `[-16.75,8.95,28.65,19.15]` | Matches after the first-layer outward twip conversion above. |
| `mc` → player | `mc` matrix `(1,0,0,1,1,-23.95)` → `[-14.75,-44.75,11.9,0]` | `mc` matrix `(1,0,0,1,-0.55,-23.7)` → `[-17.3,-14.75,28.1,-4.55]` | Exact integer-twip translations. |
| Player → `game` | P2 matrix `(-1,0,0,1,350,-25)` → `[338.1,-69.75,364.75,-25]` | P1 matrix `(1,0,0,1,310,-25)` → `[292.7,-39.75,338.1,-29.55]` | Exact mirror/translation; matches captured `getBounds(game)`. |
| `game` → `_root` | Raw matrix result `[322.56977,267.07846,373.33717,352.32579]`; observed `[322.6,267.1,373.35,352.3]` | Raw `[236.08421,324.22751,322.56977,343.65819]`; observed `[236.1,324.25,322.6,343.65]` | This target-space result does not fit one consistent floor/ceil/nearest rule from the logged `game` AABB. The hit-test comparison uses the `game`-space boxes above, so `_root` bounds are not substituted for them. |

At tick 13, the public `getBounds(game)` results are Rukia `[287.7,-39.75,333.1,-29.55]` and Yihu `[338.1,-69.75,364.75,-25]`: a 5 px horizontal gap, with the original `hitTest` returning `false`. At tick 14, the returned game-space boxes meet at x=338.1, their vertical intervals overlap by 10.2 px, and the original `bdmn.hitTest(k1atm)` returns `true`. These are observations in the coordinate space requested from the public `getBounds` API; they do not establish the internal coordinate space or rounding path used by `hitTest`.

## Interpretation boundary

This identifies the first fractional-twip conversion visible in the sampled public `getBounds` chain for this axis-aligned Rukia/Yihu pair. The actual `hitTest` booleans are captured independently; agreement with public bounds does not prove that `hitTest` uses those returned boxes or the `game` coordinate space internally. The `_root` bounds and concatenated matrices are separate observations and are not evidence for excluding that space. This sample does not establish a rounding rule for rotated/sheared matrices or all fighters. Do not modify the shared runtime from these public-bound observations alone or add an epsilon to the hit predicate; broader use needs controlled source-shape/matrix cases that compare the actual `hitTest` result.
