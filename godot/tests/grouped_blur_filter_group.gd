extends "res://filter_group.gd"
const INTEGER_BLUR = preload("res://tests/integer_blur.gdshader")
const CONSUMPTION = preload("res://tests/consumed_extent_filter_group.gd")

func _ready() -> void:
	var filters: Array = get_meta("flash_filters")
	assert(filters.size() == 1 and filters[0].type == "BLURFILTER")
	super._ready()
	# Keep production-created nodes/allocation; explicitly reconnect the measured pass order.
	var input: Texture2D = $Contents.get_texture()
	var ordered: Array[Node] = []
	for axis in 2:
		for child in get_children():
			if child is SubViewport and child.name.begins_with("FilterPass"):
				if int(child.get_meta("flash_filter_axis")) == axis:
					ordered.append(child)
	for child in ordered:
		child.get_child(0).texture = input
		input = child.get_texture()
		move_child(child, get_child_count() - 1)
	$Composite.texture = input

func _update_buffer() -> void:
	super._update_buffer()
	for child in get_children():
		if not child is SubViewport or not child.name.begins_with("FilterPass"):
			continue
		assert(int(child.get_meta("flash_filter_index")) == 0)
		var material: ShaderMaterial = child.get_child(0).material
		var amount := float(material.get_shader_parameter("blur_size"))
		var axis := int(child.get_meta("flash_filter_axis"))
		var consumed: float = CONSUMPTION.consumed_kernel(amount)
		assert(consumed >= 1.0 and consumed * 32.0 == floorf(consumed * 32.0))
		material.shader = INTEGER_BLUR
		material.set_shader_parameter("blur_size", consumed)
		material.set_shader_parameter("direction", Vector2.RIGHT if axis == 0 else Vector2.DOWN)
