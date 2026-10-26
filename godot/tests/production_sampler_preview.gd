extends "res://timeline_preview.gd"
# Opt-in test subclass, never instantiated by production scenes.
const Sampler = preload("res://tests/bitmap_sampler_diagnostic.gd")
var diagnostic_leaves: Array[Sprite2D] = []

func _apply_blend(item: CanvasItem, blend: int, copy_parent: Node = null) -> void:
	if copy_parent != null:
		# Preserve the actual production group composition, including normal blend.
		super._apply_blend(item, blend, copy_parent)
		return
	assert(item is Sprite2D and blend == 1 and item.modulate == Color.WHITE)
	assert(item.transform == Transform2D.IDENTITY)
	var texture: Texture2D = item.texture
	if texture is AtlasTexture:
		assert(texture.region == Rect2(Vector2.ZERO, texture.atlas.get_size()))
		texture = texture.atlas
	assert(texture.resource_path == "res://generated/fighters/yulong/148.png")
	assert(texture.get_size() == Vector2(34, 3))
	var material := ShaderMaterial.new()
	material.shader = load("res://tests/production_bitmap_sampler.gdshader")
	material.set_shader_parameter("source_texture", texture)
	material.set_shader_parameter("source_size", texture.get_size())
	item.material = material
	diagnostic_leaves.append(item)

func bind_allocated_buffers() -> Array:
	assert(diagnostic_leaves.size() == 1)
	var records: Array = []
	for leaf in diagnostic_leaves:
		var contents: SubViewport = leaf.get_parent()
		var group: Node2D = contents.get_parent()
		assert(contents.name == "Contents" and group.get_script().resource_path == "res://filter_group.gd")
		assert(leaf.transform.x == Vector2.RIGHT and leaf.transform.y == Vector2.DOWN)
		var bounds := leaf.transform * leaf.get_rect()
		assert(bounds == Rect2(2, 2.5, 34, 3))
		assert(contents.size == Vector2i(38, 8))
		var metadata := Image.create(contents.size.x, contents.size.y, false, Image.FORMAT_RGBAF)
		for y in range(floori(bounds.position.y), ceili(bounds.end.y)):
			var row := Sampler.row({"repeat": false, "width": 34, "height": 3,
				"sx": 1, "sy": 1, "tx": bounds.position.x, "ty": bounds.position.y,
				"y": y, "left": int(bounds.position.x), "right": int(bounds.end.x), "shape_left": 0})
			for x in range(int(row.left), int(bounds.end.x)):
				var index := x - int(row.left)
				var coverage := (minf(x+1, bounds.end.x)-maxf(x, bounds.position.x)) * (minf(y+1, bounds.end.y)-maxf(y, bounds.position.y))
				metadata.set_pixel(x, y, Color(row.xs[index], row.y, row.modes[index], coverage))
		leaf.material.set_shader_parameter("sample_metadata", ImageTexture.create_from_image(metadata))
		leaf.material.set_shader_parameter("buffer_size", Vector2(contents.size))
		var composite: Sprite2D = group.get_node("Composite")
		var global_origin := group.global_transform * composite.position
		assert(global_origin == Vector2(281, 196))
		var passes: Array = []
		for child in group.get_children():
			if child is SubViewport and child.name.begins_with("FilterPass"):
				assert(child.size == contents.size)
				passes.append({"name": child.name, "size": [child.size.x, child.size.y]})
		records.append({"texture": "res://generated/fighters/yulong/148.png", "buffer": [contents.size.x, contents.size.y],
			"source_bounds": [bounds.position.x, bounds.position.y, bounds.size.x, bounds.size.y],
			"global_origin": [global_origin.x, global_origin.y], "filter_passes": passes,
			"composite_shader_sha256": composite.material.shader.code.sha256_text(), "production_admitted": false})
	return records
