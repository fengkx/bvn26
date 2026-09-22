# Production base-roster release r01

By user direction, the production character selector now includes only the base forms 白哉 (`byakuya`) and 小李 (`lee`) in addition to its prior roster. No transform or WKframe form was opened. Both use the same `available.json` filter in VS Human and VS Com; original cards and opening-state maps were already present.

The selector source registry exposes 11 fighters and 4 helpers. Source-backed portraits and footer name textures were rebuilt from the locked `game/main.swf` with JPEXS 26.2.1. The new portrait labels are frame 9 for 白哉 and frame 28 for 小李, with five generated source-raster states each. `roster-release.json` binds source, generator, output-manifest, and new PNG SHA-256 values.

The source registry and generated artifacts were checked with:

```sh
python3 -m unittest tools.tests.test_selection_registry tools.tests.test_intro_roster tools.tests.test_selection_portrait_alpha -v
```

The native `roster_candidate_flow_smoke.gd -- --base-forms` and a fresh local Web export are delegated to integration. Opening these forms is a roster availability decision, not a claim that full character parity has passed. Coverage remains `partial`; the incomplete audiovisual, complete AI/input, and end-to-end browser boundaries remain open.
