extends "res://filter_group.gd"
# Bounded diagnostic only: authored geometry remains unchanged.
func buffer_padding() -> Vector2:
	var filters: Array = get_meta("flash_filters")
	assert(filters.size() == 1 and filters[0].type == "GLOWFILTER" and filters[0].passes == 1)
	var bounds := source_bounds()
	assert(bounds.position == bounds.position.floor() and bounds.size == bounds.size.floor())
	return Vector2(floorf(float(filters[0].blurX) / 2.0) + 1.0,
		floorf(float(filters[0].blurY) / 2.0) + 1.0)

func _update_buffer() -> void:
	super._update_buffer()
	# The bounded candidate includes the far endpoint, without changing source bounds.
	$Contents.size += Vector2i.ONE
	for child in get_children():
		if child is SubViewport and child.name.begins_with("FilterPass"):
			child.size = $Contents.size
