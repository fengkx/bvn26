extends "res://tests/grouped_family_filter_group.gd"
const SHADOW_BYTES = preload("res://tests/integer_shadow.gdshader")

func _ready() -> void:
	super._ready()
	var spec: Dictionary = get_meta("shadow_diagnostic")
	assert(spec.strength * 256 == floorf(spec.strength * 256))
	for child in get_children():
		if child is SubViewport and child.name.begins_with("FilterPass") and int(child.get_meta("flash_filter_index")) == -1:
			var material: ShaderMaterial = child.get_child(0).material
			var original: Texture2D = material.get_shader_parameter("original_texture")
			var offset: Vector2 = material.get_shader_parameter("shadow_offset")
			material.shader = SHADOW_BYTES
			material.set_shader_parameter("original_texture", original)
			material.set_shader_parameter("shadow_offset", offset)
			material.set_shader_parameter("color_bytes", Vector4i(spec.color[0], spec.color[1], spec.color[2], spec.alpha_byte))
			material.set_shader_parameter("strength_256", int(spec.strength * 256))
			material.set_shader_parameter("apply_filter_api", spec.api == "apply")
			material.set_shader_parameter("source_hidden", spec.hidden)
