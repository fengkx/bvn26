# Complex solid-paint source audit

## Sage Naruto source-first answers

1. `scripts/fighter/minrenx.json`, BODY `DefineSprite_449`: down-special enters
   the authored ultimate at frame 875. `minrenx-source.json.gz` retains every
   frame, placement/MOVE and numbered action through frame 990. Nested vector
   shape/display definitions are retained in `minrenx-geometry.xml.gz`.
2. The retained display list places the ultimate's nested effect graph, whose
   frame changes select shapes 344–367. Each shape's authored directed edges,
   style table, transforms and alpha remain source inputs. Missing geometry
   currently makes the renderer paint bounds instead of these edges.
3. BODY frame 968 executes `gotoAndStop("收"); play();`. Removal and subsequent
   playback follow the existing display list; compiling paint does not alter it.
4. Preserve the source even-odd/nonzero fill rule, holes, shared edge ownership,
   paint colors, transforms and opacity. An outer bounding rectangle cannot
   represent the wind arcs. Triangulation is import-time geometry, not a
   character-specific runtime effect.
5. The unchanged 420-tick fixture was run in native Flash and native Godot.
   At fight tick 205, Flash displays separate wind arcs while Godot obscures
   the scene with a cyan rectangle. At tick 175, Godot also overfills the lower
   wind effect. Corresponding before/source PNGs are retained here. All 842
   actor states and 421 root positions match; this is a rendering defect.

## Ichigo Bankai follow-up

The ultimate is BODY `DefineSprite_1180`, frames 622–726; frame 717 jumps to
`站立` and resumes. Shapes 1034/1037 have joined curved edges. Complete BODY
scripts/placements and the relevant nested graph are retained. Existing sampled
frames 145/175 do not establish a visible rectangle for these shapes; denser
samples around the frame-648 placement are required before regenerating this
form's geometry.

## Geometry references

The fill flag maps to even-odd (0) or nonzero (1), as documented by the
[Apache Flex SWF compiler](https://flex.apache.org/maven/flexjs/latest-dev/compiler/apidocs/org/apache/flex/compiler/internal/fxg/dom/types/Winding.html).
Shapely's node/polygonize operations resolve touching/intersecting linework;
its constrained Delaunay triangulation preserves polygon boundaries and holes.
See the [Shapely source](https://github.com/shapely/shapely/blob/main/src/shapely/constructive.py).

## Sage Naruto repair and validation

The importer now polygonizes directed solid edges and selects faces using the
source winding rule before constrained triangulation. This handles nested holes
and shared junctions that the simple contour compiler cannot represent. Godot
renders the resulting indexed triangles through its existing Polygon2D path.
Shapely 2.1.2 / GEOS 3.13.1 runs only during import.

The base timeline and embedded AI geometry were refreshed; stripping the three
paint-geometry fields leaves the AI context identical. Source colors, opacity,
placement, frame actions and combat fields are unchanged. Form package hashes
were refreshed after checking this difference.

`minrenx-after-175.png` and `minrenx-after-205.png` show the wind arcs without the
large rectangle. `minrenx-after-comparison.json` retains exact matches for all
842 actor states and 421 root positions on the original unchanged input.
The top HUD is still absent at some sampled native frames; this separate
presentation difference remains under investigation and is not a parity pass.

Validation: 16 solid/bitmap geometry tests, native rendered replay, contract
validation, input-integrity verification and handoff checks passed. No original
input files or comparison thresholds were changed.
