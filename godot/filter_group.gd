extends "res://blend_group.gd"

const FILTER_SHADER = preload("res://flash_filter.gdshader")


func _ready() -> void:
	# A snapshot duplicates nodes but must sample its own viewport textures.
	for child in get_children():
		if child.name.begins_with("FilterPass"):
			remove_child(child)
			child.queue_free()
	super._ready()
	var texture: Texture2D = $Contents.get_texture()
	for filter: Dictionary in get_meta("flash_filters", []):
		var original := texture
		if filter.type in ["BLURFILTER", "GLOWFILTER"]:
			for pass_index in int(filter.passes):
				for axis in 2:
					var amount := float(filter.blurX if axis == 0 else filter.blurY)
					if amount <= 1.0:
						continue
					texture = _filter_pass(texture, {"operation": 0, "blur_size": amount,
						"direction": Vector2.RIGHT if axis == 0 else Vector2.DOWN})
		if filter.type == "GLOWFILTER":
			var color: Array = filter.color
			texture = _filter_pass(texture, {"operation": 1, "original_texture": original,
				"glow_color": Vector4(color[0], color[1], color[2], color[3]),
				"glow_strength": float(filter.strength)})
		elif filter.type == "COLORMATRIXFILTER":
			var values: Array = filter.matrix
			var uniforms := {"operation": 2,
				"offsets": Vector4(values[4], values[9], values[14], values[19]) / 255.0}
			for row in 4:
				var i := row * 5
				uniforms[["row_r", "row_g", "row_b", "row_a"][row]] = Vector4(values[i], values[i + 1], values[i + 2], values[i + 3])
			texture = _filter_pass(texture, uniforms)
	$Composite.texture = texture


func _filter_pass(input: Texture2D, uniforms: Dictionary) -> Texture2D:
	var viewport := SubViewport.new()
	viewport.name = "FilterPass%d" % get_child_count()
	viewport.transparent_bg = true
	viewport.world_2d = World2D.new()
	viewport.size = $Contents.size
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	var sprite := Sprite2D.new()
	sprite.centered = false
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	sprite.texture = input
	var material := ShaderMaterial.new()
	material.shader = FILTER_SHADER
	for key in uniforms:
		material.set_shader_parameter(key, uniforms[key])
	sprite.material = material
	viewport.add_child(sprite)
	add_child(viewport)
	return viewport.get_texture()


func buffer_padding() -> Vector2:
	var padding := Vector2.ZERO
	for filter: Dictionary in get_meta("flash_filters", []):
		if filter.type in ["BLURFILTER", "GLOWFILTER"]:
			padding += Vector2(ceilf(maxf(0.0, (float(filter.blurX) - 1.0) / 2.0)),
				ceilf(maxf(0.0, (float(filter.blurY) - 1.0) / 2.0))) * int(filter.passes)
	return padding


func _update_buffer() -> void:
	super._update_buffer()
	for child in get_children():
		if child is SubViewport and child.name.begins_with("FilterPass"):
			child.size = $Contents.size
