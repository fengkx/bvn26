# Byakuya HUD clock source audit r01

This artifact answers the five SOURCE_FIRST questions for the shared HUD clocks without changing production code. The source qitiao callbacks live in `DefineSprite_1774` and `DefineSprite_1782`, sample `ql` on a 300 ms interval, and select `qt`/`bss`. The countdown is a separate `DefineSprite_1813` 1000 ms interval with its own pause/alive rules.

The qt301 nested sprite 1763 is an independent authored child timeline. A parent frame selection is not a valid substitute for observing its local frame. The proposed observer must use the same-input fixture and record real callback, display, fight, pause, and child-clock events. It must reject direct `goto`, injected ql/child frames, missing snapshots, and wall-clock-only alignment.

Current acceptance boundary: source mapping and focused authored HUD rendering are evidenced elsewhere; real 300 ms callback phase, pause behavior, nested qt301 clock, and countdown lifecycle remain pending.

Source and generated hashes are recorded in `audit.json`.
