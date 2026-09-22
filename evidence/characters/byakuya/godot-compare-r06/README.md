# Godot same-input comparisons r06

Each compare covers the 14 source state fields (`frame`, `x`, `y`, `xscale`, `action`, `hp`, `ql`, `sw`, `touch`, `touchFloor`, `hits`, `paused`, `hstm`, `hurtSkling`) across 602 source and 602 runtime rows.

`airhit`, `bisha-below`, `bisha-exact`, `defence`, and r04 ordinary hit are matched with zero differences. `air-special` has 602/602 field matches but remains unaccepted because its runtime log contains 15 projectile guard assertions; the source/runtime comparison alone does not suppress runtime errors.
