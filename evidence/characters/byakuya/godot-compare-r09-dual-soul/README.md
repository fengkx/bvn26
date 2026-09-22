# Byakuya special neutral r09 (dual-soul)

All five captures were rebuilt from the same fixtures with explicit `p1-helper=魂` and `p2-helper=魂`. Each native trace records both `helper_load` values as `魂,kon.swf`; the prior Sword+Soul r03 captures are invalid for this fixture and are excluded.

- `必杀` frame 454: matched 602/602.
- `上必杀` frame 576: matched 602/602.
- `超必杀` frame 690: matched 602/602.
- `空中必杀` frame 455: different 602/602; first difference tick 21, p1 `ql`, original 300 vs Godot 200; 280 differences.
- `招换` frame 814: different 602/602; first difference tick 29, p1 `paused`, original true vs Godot false; 526 differences.

The comparison JSON and compressed native event traces are stored beside this file. These are focused same-input comparisons, not full character parity.
