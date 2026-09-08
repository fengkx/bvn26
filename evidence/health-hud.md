# HP HUD source and validation

Implemented 2026-09-08; source-derived presentation, not full original-player parity acceptance.

## Source gate

- `scripts/main.json` / `DefineSprite_1814/frame_1/DoAction.as` is the only frame script of the single-frame HP container. It selects `namemc` portraits and installs `onEnterFrame`: instantaneous HP percentage, early return when either HP is zero, sticky `kk` frame 2 below 20%, and `bar2` following only when victim `hits == 0`. The decrement is `maxhp / 500` percentage points, with next-frame snap after overshoot. `xuntiaoInitlize` resets both layers and warning frames.
- Main XML `xuetiao` is a new placement of sprite 1815 at root depth 71. Sprite 1815 contains a new 1814 at depth 33 on frame 1, then MOVE transforms; frames 1 and 5 stop. The active layout uses frame 5 and composes the root transform. Sprite 1814 is a persistent single-frame container; there is no attack-label exit or per-hit recreation.
- Shapes 591, 1787, 1792, 1796, 1812 are rasterized by pinned JPEXS 26.2.1. Warning sprite 1788 exports all 20 frames. Portraits use the already extracted sprite 1465 labels and source shape 1797 mask, including quadratic edges. Curves are sampled into 16 segments each; cross-renderer edge rasterization remains unverified.
- Tests assert source percentages, trail hold during hits, chase after hits, zero-HP early return, and reset. Existing fighter damage is unchanged. The legacy debug `displayed_health` field is not the HUD oracle.
- Original reference: the user-provided screenshot establishes placement, artwork, and visible damage direction. No identical-input original-player trace was captured; M2/M3 parity remains pending. Entrance/exit tween, round-win markers, and timed-mode digits are outside this current untimed battle slice.

## Checks

- `godot --headless --path godot -s res://tests/health_hud_smoke.gd`: `HEALTH_HUD_SMOKE_OK`.
- Native Godot 4.7.2 rendered capture `/tmp/bvn-hp-hud.png`: manually inspected portraits, left full HP, right 65% HP with full delayed red layer, and infinity icon. The 65% value is a synthetic display fixture, not an original replay.
- `python3 tools/verify.py` and `python3 tools/check_handoff.py`: passed.

## Rebuild

```sh
python3 tools/importer/build_health_presentation.py --workspace /tmp/main-pinned --ffdec-jar /tmp/ffdec-26.2.1/ffdec.jar --raster-workspace /tmp/hp-raster --output godot/generated/main/health
```

Source SWF hash and source placements are saved in `godot/generated/main/health/presentation.json`. Temporary raster workspaces are not shipped.
