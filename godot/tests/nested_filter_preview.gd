extends "res://timeline_preview.gd"
# Diagnostic only: actual production group allocation with integer composition
# at every leaf and materialized buffer boundary. Never instantiated by gameplay.
var diagnostic_groups: Array[Node] = []

func _apply_blend(item: CanvasItem, blend: int, copy_parent: Node = null) -> void:
	assert(blend == 1 and item is Sprite2D and item.modulate == Color.WHITE)
	var multiplier := 256
	var post_mul := Vector3.ONE
	var post_add := Vector3.ZERO
	if copy_parent != null:
		assert(item.material is ShaderMaterial)
		assert(item.material.get_shader_parameter("cached_opacity") == true)
		post_mul = item.material.get_shader_parameter("post_mul")
		post_add = item.material.get_shader_parameter("post_add")
		multiplier = floori(float(item.material.get_shader_parameter("group_opacity")) * 256.0)
		diagnostic_groups.append(copy_parent)
	var material := ShaderMaterial.new()
	material.shader = load("res://tests/nested_filter_composite.gdshader")
	material.set_shader_parameter("opacity_multiplier", multiplier)
	material.set_shader_parameter("post_mul", post_mul)
	material.set_shader_parameter("post_add", post_add)
	item.material = material
	var copy := BackBufferCopy.new()
	copy.name = "DestinationCopy"
	copy.copy_mode = BackBufferCopy.COPY_MODE_VIEWPORT
	copy.show_behind_parent = true
	item.add_child(copy)
