# helper_repeat_contact baseline classification

The original fixture was run against the repository HEAD helper runtime and
again against the current helper FIFO runtime. Both failed at line 30 with
the same assertion: `Flash helper hitTest includes touching edges`.

The failure was in the fixture construction, not the hit-test boundary. The
single correction left a measured 0.04998779296875px gap after transformed
twip-to-pixel rounding. The corrected fixture now recomputes live transformed
bounds twice before asserting touching contact, then moves +0.05px for the
strict negative case. The positive observations record an exact `gap == 0.0`;
the negative observations record positive gaps of about 0.05px per case. It
passes as `HELPER_REPEAT_CONTACT_SMOKE_OK` in
`current-fixed-fixture.log` without changing the runtime threshold.

The source geometry is the generated Woailuo frame 44 `atm1` placement
(character 48, depth 2, translateX=3437 twips, translateY=-1783 twips), and
the existing source-derived `intersects(..., true)` edge rule remains intact.
The original red logs are retained as provenance; they are not passing
evidence for the FIFO change.
