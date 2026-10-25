# r160 — affine coefficients feasible, common initialization still rejected

Native coordinate-coded source channels provide **44522 independent source-index inequalities** from r158 fully covered pixels. The r159 clipped samples reproduce the same pixels exactly, so clipping does not justify a second route. Each inequality is half-open: index <= A*x+B*y+T < index+1.

For both exact inverse and16.16 inverse coefficients, all **320/320 per-axis intercept intervals are nonempty**. This is a feasibility/rejection result, not an estimated coefficient. No interval endpoint or midpoint is used to render.

Independently defined intercept constructions all fail global bounds. Exact center passes128/320 intervals; fixed center and fixed rounded half-step pass144/320. Corner, horizontal-center and vertical-center alternatives also fail. The evidence retains exact rational bounds and their lower/upper witness coordinates. No per-transform fitted intercept or RGB-selected route is admitted.

[Summary](summary.json), [all rational intervals/witnesses](intervals.json.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.analyze_nearest_affine_intervals --native evidence/importer-loud-fail/r158/native --output /tmp/nearest-intervals.json
python3 -m unittest tools.tests.test_nearest_affine_intervals
```

Next discriminator: realize the same source-to-device matrix through child-transform versus bitmap-fill-transform paths. Preserve source bytes, effective transform readbacks, authored contours and independent clip geometry. Compare interior source indices before proposing another initializer. This separates transform composition/geometry consumption from an arbitrary intercept fit. Keep all existing controls and interval rejections.

`coefficients_selected_from_intervals=false`, `affine_sampler_admitted=false`, `production_admitted=false`. Existing24 diagnostic images remain exact; production54 historical9/54; AS ownership remains open. Draft only; no merge/deploy/Worker.
