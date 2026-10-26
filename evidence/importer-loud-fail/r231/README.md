# r231: scalar-width clips do not remove the persistent initializer failures

No new capture. Compare all six fixed-HV coordinate models against width1 clips at starts46/47/48 and the omitted full baseline at exactly the same geometry-selected coordinates. Source bytes and matrices remain pinnedr230; no model is selected by clip or RGB. Fullr229/r230 failures remain linked by SHA.

Scaled-child/minimum HV: full **3944/4320**, scalar-width **3923/4320**. Of the same coordinates,375fail both,1is repaired,22new failures appear. Native full/scalar outputs themselves agree4277/4320, leaving43changes.

- Shape56 authored minifying scale: horizontal and vertical ramp groups remain0/27 for each cache state; full/scalar native pixels agree27/27. The large error survives this scan-width isolation.
- Shape56 scale1 uncached ramps: full153/153 each, scalar151/153 horizontal and148/153 vertical.
- Shape57 scale1 vertical ramp: full/scalar both60/153, with persistent errors.

A scalar clip does not justify an offset patch or an initializer claim. All six models remain rejected; no production/GPU/native change. Source-backed complete diagnostic coverage46/54, historical production9/54; AS/clip-action ownership remains open.

## Reproduce

```sh
python3 -m tools.probes.analyze_jinye_scalar_clips --output /tmp/bvn-r231/analysis.json
python3 -m unittest tools.tests.test_jinye_scalar_clips
```

Focused tests3/3; mandatory gates in acceptance.json/checks. Retained fullPython1011pass/2skip. Production roster/Web/54suite not rerun because runtime is unchanged. Candidate/GPU/production admission false.

## Next discriminator

Retain authored geometry/fill matrix/child/outer/draw transforms. Independently generate coordinate-coded source bytes (R=2x,G=6y,B73,A255), capture authored smooth65 and an explicit nearest67 countercontrol changing only the active fill-type byte. Preserve original references and document exact raw-tag byte differences. Include full and the same single-column clips, both cache states. First verify smooth red/green channels against pinned separate ramps; then use geometry-selected nearest source-code readbacks to constrain source cells independently. Record non-texel/cache-postprocessing results rather than dropping them. No coordinate or offset may be chosen from locally matching RGB.
