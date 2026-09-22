# Godot 576 runtime render-node audit

The probe emitted `runtime-display-list.json` from the live `FighterRuntime` at source frame 576, capture tick 286. It includes the five live source placements and 3867 actual render nodes (Polygon2D/Sprite2D) with local/global Transform2D, z-index, and texture path.

The five direct placement dictionaries match the source mapping in the r02 audit. Render nodes are recursive shape/bitmap draw primitives rather than one node per source MovieClip; therefore this artifact is the runtime transform inventory for the later GUI crop comparison, not a claim that node count equals the Flash display list.

SHA256: `10e8d15363a8cbeb8428dffbd48c552a2e680b1267cf58f46dfc593428054340`
