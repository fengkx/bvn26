# Arcade campaign

The native Flash Player trace in `routes.tsv` records the output of the original
`gostg` function in game/main.swf for every selectable fighter and each of the
eight zero-based stage indices. The probe iterated the inputs and recorded the
opponent, helper and map after each call. It did not simulate 320 battles.

Run `python3 -m unittest tools.tests.test_arcade_routes` to compare those records
with the campaign consumed by Godot. Run Godot with `--headless --path godot
--script res://tests/arcade_flow_smoke.gd` for title navigation, tutorial skip,
selection, eight stages, transformed rivals, continue, game over and credits.
