extends "res://filter_group.gd"
# Diagnostic-only allocation from independently captured native rectangle metadata.
func buffer_padding() -> Vector2:
	var filters: Array = get_meta("flash_filters")
	assert(filters.size() == 1 and filters[0].type == "GLOWFILTER")
	assert(filters[0].blurX == 5 and filters[0].blurY == 5 and filters[0].passes == 1)
	var measured: Rect2 = get_meta("native_filter_rect")
	var source := source_bounds()
	var padding := source.position - measured.position
	assert(padding.x >= 0 and padding.y >= 0)
	assert(measured == source.grow_individual(padding.x, padding.y, padding.x, padding.y))
	return padding
