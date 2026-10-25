# r195 — identity post-CXFORM exposes ColorMatrix RGB differences

Capture original white and identity owner states with complete source/property/clock/restoration checks. Each isolated SWF rebases only its synthetic diagnostic wrapper ID60001/60002→60000; original source symbols, placements, filters and pinned reference images are unchanged. The initial combined-family wrapper-ID assertion rejected until this explicit local namespace adaptation was added.

The live actual-FilterGroup family now matches **10/12 pinned final images**. Blue4/4 and white4/4 are exact; identity empty frames are exact, but identity active tick0/tick8 differ **2423/530 pixels,maxchannel delta1**. The command correctly exits1; `full_family_exact=false`.

Identity native captures independently expose raw cache RGB: all12 local/Contents comparisons are **652944/652944 RGBA pixels exact**, across the six active cases. Therefore the remaining error belongs after the proved sampler/cache input. Filtered RGB repeats the2423/530 differences in all three post-transform states; blue/white conceal those RGB differences through their authored zero multipliers. No intermediate success was inferred from them.

[Strict GPU report/all coordinates](gpu/report.json), [fixture](gpu/fixture.json), [native state2/state3 captures](native), [native provenance](provenance.json), [GPU provenance](gpu/provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.build_matrix_owner_family --cases evidence/importer-loud-fail/r32/components/main/cases.json --output /tmp/matrix-owner-family --ffdec /path/to/ffdec-cli.jar
# Capture each frame2/frame3/components/main folder with capture_native_player.py.
python3 -m tools.probes.run_nearest_matrix_family --godot /path/to/Godot --native evidence/importer-loud-fail/r195/native --output /tmp/nearest-matrix-family
python3 -m unittest tools.tests.test_nearest_matrix_family
```

Next discriminator: use the now-proved raw cache RGBA and native identity-filter output to isolate ColorMatrix byte arithmetic. Compare globally fixed coefficient precision, unpremultiplication and final byte conversion against the old scalar/ramp controls as well as these boundaries. If several sequences agree, capture explicit source-byte ramps with the authored20 coefficients before changing any shader. No per-pixel formula selection or tolerance.

`full_family_exact=false`, `production_admitted=false`. Source-backed exact live-image union28→34 (includes two newly compared empty images); production54 historical9/54, not rebound. Full AS/clip-action ownership remains separate. Draft only; no production changes.
