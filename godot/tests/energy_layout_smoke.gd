extends SceneTree

# Focused source-layout regression: frame 5 is the visible HUD placement and
# both sides must consume the compiled root/1815 matrices.
func _init() -> void:
	var bar = preload("res://energy_bar.gd").new()
	root.add_child(bar)
	await process_frame
	var p1: Transform2D = bar._source_outer_transform()
	bar.mirrored = true
	var p2: Transform2D = bar._source_outer_transform()
	assert(is_equal_approx(p1.origin.x, 6.35))
	assert(is_equal_approx(p1.origin.y, 364.45))
	assert(is_equal_approx(p1.x.x, 0.6065521))
	assert(is_equal_approx(p2.origin.x, 591.8))
	assert(is_equal_approx(p2.origin.y, 364.45))
	assert(is_equal_approx(p2.x.x, -0.6065521))
	assert(absf(float(bar.custom_minimum_size.x) - 144.784) < 0.01)
	assert(absf(float(bar.custom_minimum_size.y) - 36.99968) < 0.01)
	bar.energy = 300.0
	bar.advance_display_tick(100)
	var nested_frame := int(bar._qt_child_frame)
	bar.advance_display_tick(100)
	assert(int(bar._qt_child_frame) == nested_frame)
	bar.advance_display_tick(101)
	assert(int(bar._qt_child_frame) == (nested_frame % 10) + 1)
	print("HUD_LAYOUT_SMOKE_OK ", JSON.stringify({"p1_origin": p1.origin, "p2_origin": p2.origin, "min_size": bar.custom_minimum_size}))
	quit()
