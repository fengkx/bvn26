# r142 — original Lanran animated fill graph retained; input remains rejected

All nine source frames, replacement placement tags, inherited identity inner matrices and complete wrapper XML are retained. Shapes8/10/12 use bitmaps7/9/11 at35×65,34×63,36×64. Each complete fill table has an unused slot and one active four-edge rectangle; directed edge ownership is checked before creating a renderer view. Original masks, slots, matrices and raw source tag hashes remain in the fixture. Unknown action/display tags, named/clip placements, affine fills, curves and unproven encodings reject.

Native frame clocks select source shapes8/10/12/8 at ticks0/4/8/11. The unchanged admitted positive-axis cache model does **not** pass this source:

| Tick/source frame/shape | Cache exact | Filtered exact | Pinned final exact |
|---|---:|---:|---:|
|0/1/8|239338/240000|239450/240000|239524/240000|
|4/5/10|hard reject: unproven fractional coverage|not rendered|not rendered|
|8/9/12|239316/240000|239405/240000|239477/240000|
|11/3/8|239338/240000|239450/240000|239524/240000|

Nonblocked input max channelΔ3 (alphaΔ2). The hard rejection has eight nontransparent fringe footprints at `game/fighter/lanran.swf:DefineSprite_13/frame_5/DefineShape_10`; the first is stage(289,231), with geometric area≈.35. The `.1/.35` local shape boundaries are outside the independently proven quarter-grid domain. The analyzer records the rejection and exits1; no guard is removed and no fallback image is generated for that frame.

[Fixture with complete source metadata](fixture.json), [summary including exact sites/footprints and deltas](summary.json), [provenance/export command](provenance.json), [acceptance](acceptance.json).

```sh
java -Djava.awt.headless=true -jar /path/to/ffdec-cli.jar -swf2xml game/fighter/lanran.swf /tmp/lanran-source.xml
python3 -m tools.probes.extract_animated_rect_component --xml /tmp/lanran-source.xml --cases evidence/importer-loud-fail/r21/components/lanran/cases.json --case lanran-640-732-32 --output /tmp/lanran-fixture.json
python3 -m tools.probes.analyze_animated_rect_component --fixture evidence/importer-loud-fail/r142/fixture.json --native evidence/importer-loud-fail/r141/native --output /tmp/lanran-source-analysis  # expected exit1
python3 -m unittest tools.tests.test_animated_rect_component
```

Next discriminator: independently vary fractional bitmap-fill translation with a fixed rectangle and single-pixel draw clips, retaining source byte readbacks and matrix properties. Separate fill-matrix translation consumption from parent/draw normalization before altering sampling; then independently vary non-quarter shape coverage. Do not fix a phase using whichever formula matches these component pixels.

`source_cpu_exact=false`, `gpu_binding_verified=false`, `production_admitted=false`. No production rendering changes. Eight bounded source-backed live images exact, historical full production54 still9/54. General coverage/affine and full AS ownership remain open. Draft only; no merge/deploy/Worker.
