# r176 — rounded minimum footprint retains every old observation

The same fixed16.16 inverse and minimum(0,a,b) geometric correction now round the Euclidean offset onto the16.16 grid. Every retained native control, including r174 dominant shears and r175 selected boundaries, is re-evaluated: **66882/66882 exact**.

Half-up, ties-even and ties-away variants all agree on these samples because **zero samples have an offset tie**. Their agreement cannot establish a tie rule. No per-pixel arithmetic selection or coefficient fitting is used; production and GPU admission remain closed pending independent tie controls.

[Summary](summary.json), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.analyze_affine_rounded_footprint --output /tmp/rounded-footprint.json
python3 -m unittest tools.tests.test_affine_rounded_footprint
```

Next discriminator: signed scale3/5/7/13 on each axis, source coordinates4/8/12, independent target origins and quarter-pixel translations bracketing exact source boundaries. Explicit source/property readbacks must distinguish positive and negative half-grid offsets without changing source bytes. Keep every old control before GPU binding; do not claim half-grid behavior from non-tie observations.

`candidate_admitted=false`, `gpu_advance_allowed=false`, `production_admitted=false`. Production54 historical9/54;24 live/wrapper diagnostic images exact. AS ownership remains open. Draft only.
