extends "res://tests/integer_extent_filter_group.gd"
const INTEGER_BLUR_SHADER = preload("res://tests/integer_blur.gdshader")

# Diagnostic operand consumption only; authored metadata and allocation stay intact.
static func consumed_kernel(value: float) -> float:
	assert(is_finite(value) and value >= 0.0)
	if value == 0.0:
		return 0.0
	var mantissa := value
	var exponent := 0
	while mantissa >= 1.0:
		mantissa *= 0.5
		exponent += 1
	while mantissa < 0.5:
		mantissa *= 2.0
		exponent -= 1
	return floorf(mantissa * 64.0) * pow(2.0, exponent - 6)

func _update_buffer() -> void:
	super._update_buffer()
	var filters: Array = get_meta("flash_filters")
	for child in get_children():
		if not child is SubViewport or not child.name.begins_with("FilterPass"):
			continue
		var index := int(child.get_meta("flash_filter_index"))
		if index < 0:
			continue
		var axis := int(child.get_meta("flash_filter_axis"))
		var amount := float(filters[index].blurX if axis == 0 else filters[index].blurY)
		var material: ShaderMaterial = child.get_child(0).material
		assert(material.shader == FILTER_SHADER or material.shader == INTEGER_BLUR_SHADER)
		material.shader = INTEGER_BLUR_SHADER
		material.set_shader_parameter("direction", Vector2.RIGHT if axis == 0 else Vector2.DOWN)
		var consumed := consumed_kernel(amount)
		assert(consumed > 1.0 and consumed * 32.0 == floorf(consumed * 32.0))
		material.set_shader_parameter("blur_size", consumed)
