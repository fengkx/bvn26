# r229: globally fixed HV improves leaves but does not admit coordinates

Six independently defined existing coordinate constructions now use horizontal-then-vertical interpolation globally. No feasible cell/fraction fromr228 is read or used. All six remain rejected on pinnedr223/r225/r227 and originalr221JPEG leaves; full residuals remain in analysis.json.gz.

Scaled-child-quarter/minimum-footprint HV results:

| Suite | Exact |
|---|---:|
| r223 independent controls |321216/329280|
| r225 translation controls |563949/686772|
| r227 amplitude controls |255751/256992|
| r227 observed red-active union |207/1184|
| Original JPEG leaves |2763/2818|

Shape57 original uncached leaf is1215/1217 (two delta1 failures); cached1198/1217 (nineteen delta1). Shape56 stays175/192 in each cache state but active0/17, max alpha delta215. No tolerance or offset patch is added.

The classification does not support blanket minification/mipmap speculation: shape56 authored-scale inverse row norms are4.016799/4.382424 with uniformly low ramp bytes; shape57 shares essentially the same second-row rate but has near-exact authored-scale ramps. Shape57 scale1 has a different +1 green residual even without either row minifying. These observations only motivate independently varying scan boundaries, not a formula chosen from RGB.

## Reproduce

```sh
python3 -m tools.probes.analyze_jinye_fixed_hv --output /tmp/bvn-r229 --dump /tmp/bvn-r215/jpeg-planes
python3 -m unittest tools.tests.test_jinye_fixed_hv tools.tests.test_jinye_impulse_weights tools.tests.test_jinye_joint_impulses
```

Old axis/repeat implementation is unchanged and retained exact regression results are underchecks. No universal HV route, cache-origin rebase, fitted phase, new native capture or GPU work. Candidate/GPU/production admission false. Complete diagnostic coverage46/54; historical production9/54. Full AS/clip-action ownership open. Mandatory gates recorded in acceptance.json; no new production roster/Web/54suite run.

## Next discriminator

Keep source bytes, raw fill65/mask and all child/outer/draw matrices fixed. Change only destination draw clipRect origin/width around the same authored sample locations: single pixel, short lengths around4,16 and full baseline. Retain both cache states and original/1x scales, explicit source/property readbacks, and compare overlapping output coordinates. This distinguishes scan-span initialization/partition effects before any further coefficient or phase hypothesis; unchanged coordinates must not be moved with the clip. Preserve near-exact shape57 and all old axis/native controls.
