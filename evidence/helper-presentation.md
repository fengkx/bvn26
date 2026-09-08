# Helper depth and MP portrait correction (2026-09-08)

Scope: the user's two screenshots show Gaara and his sand behind the fighters in
Godot, ahead of them in the original, and the missing MP-bar helper portraits.

## Source-first questions

1. `scripts/main.json`, `DefineSprite_1774/frame_1/DoAction.as` and
   `DefineSprite_1782/frame_1/DoAction.as` select `tx.namemc` using `p2sf`/`p1sf`.
   These HUD containers have one frame; their interval only updates qt/bss.
   Stage sprite 1738 puts p2/p1/p2fz/p1fz at depths 7/9/11/13. No
   `swapDepths` exists in the main script bundle. No helper action scripts changed.
2. Those stage slots are original PlaceObject2 instances, not a fresh layer on
   summon. Gaara's root timeline places atm1 at frame 44, through frame 85;
   it remains inside the helper container, so its local depths cannot interleave
   with another fighter's children. Existing PlaceObject/MOVE timing is unchanged.
3. Portrait selection is gotoAndStop on the selected name. No autonomous portrait
   playback is added. Helper frame 1 parks/stops; the existing frame 85 return
   and helper activation at frame 2 are unchanged.
4. Assertions lock the original container ordering, local subtree isolation,
   and portrait identity matching the actual helper, including mirrored spawn.
   Source tx sprite 1753 uses bitmap frame 1750, polygon mask 1751, namemc 1465,
   and outline 1752. These are compiled, not reconstructed from the screenshot.
5. The user supplied an original-player screenshot of the same summon, which
   confirms visual overlap and the portrait. A fixed-input paired frame trace
   was not captured in this change; full one-to-one validation remains pending.

## Implementation and rebuilding

`build_helper_presentation.py` reads the pinned main XML and uses the existing
materializer for original PNG/alpha. It emits portrait label mapping, mask,
outline, affine transforms, source hash, and stage depths. Run:

```sh
python3 tools/importer/build_helper_presentation.py --workspace /tmp/main-pinned --output-dir godot/generated/main/helper_portraits
```

The renderer traverses each depth-sorted subtree contiguously rather than adding
nested depths. The stage retains its root depths to interleave actors with its
foreground. Actor nodes use the compiled source slot depths. MP bars display the
actual helper ID (currently P1 Gaara, P2 Kon), with the original masked portrait.

## Validation

See `godot/tests/helper_presentation_smoke.gd` for source-order and identity
assertions and optional rendered capture at `/tmp/bvn-helper-presentation.png`.
Full M1/M2/M3 acceptance remains pending; this change does not complete a milestone.

Executed with Godot 4.7.2: helper presentation smoke passed headless and with the
macOS renderer. The rendered frame 60 shows Gaara ahead of Naruto and the sand
covering Ichigo; both MP portraits render with the original polygon crop.
`combat_smoke.gd` passed; Python discovery passed 40 tests. `verify.py`,
`check_handoff.py`, and `.venv/bin/python tools/validate_contracts.py` passed.
Web export rebuilt `dist/web/index.html` and its package. Sandboxed export emitted
an editor-settings save warning outside the workspace; package export completed.
The rendered check was native Godot, not a new browser gameplay run.

Follow-up Web check: the rebuilt package reached `M0_BOOT_OK` and the menu in the
Codex Chromium in-app browser via a loopback HTTP server. Background capture was
black until the tab was made visible. Automated key presses did not advance the
menu, so this is a Web boot check only, not a browser summon acceptance result.
The overlap and portrait visual acceptance above uses the native renderer.
