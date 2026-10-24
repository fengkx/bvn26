extends SceneTree
const Preview = preload("res://tests/nested_buffer_preview.gd")
var views: Array[SubViewport] = []
var records: Array = []
var groups: Array = []

func _initialize() -> void:
	_run.call_deferred()

func _sprite(pixel: Array, size: Vector2i, position: Vector2) -> Sprite2D:
	var image := Image.create(size.x, size.y, false, Image.FORMAT_RGBA8)
	image.fill(Color8(pixel[0], pixel[1], pixel[2], pixel[3]))
	var sprite := Sprite2D.new()
	sprite.texture = ImageTexture.create_from_image(image)
	sprite.centered = false
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	sprite.position = position
	return sprite

func _add(preview: Node, pixel: Array, size: Vector2i, position: Vector2) -> void:
	var sprite := _sprite(pixel, size, position)
	preview._apply_blend(sprite, 1)
	preview.add_child(sprite)

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 3)
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	assert(fixture.production_admitted == false and fixture.cases.size() == 432)
	assert(args[2] in ["fresh", "stale"])
	for spec: Dictionary in fixture.cases:
		var view := SubViewport.new()
		view.size = Vector2i(16, 8)
		view.transparent_bg = true
		view.world_2d = World2D.new()
		view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(view)
		var preview := Preview.new()
		preview.autoplay = false
		preview.play_timeline_sounds = false
		preview.show_collision_shapes = false
		# Build before adding to the tree so both nested group _ready callbacks
		# bind their own actual production Contents textures after reparenting.
		_add(preview, spec.inputs.back, Vector2i(16, 8), Vector2.ZERO)
		_add(preview, spec.inputs.middle, Vector2i(12, 8), Vector2(2, 0))
		_add(preview, spec.inputs.leaf_a, Vector2i(8, 8), Vector2(4, 0))
		_add(preview, spec.inputs.leaf_b, Vector2i(4, 4), Vector2(6, 2))
		preview._compose_blend_group(2, float(spec.key[3])/100.0, 0, 1, [], true)
		preview._compose_blend_group(1, float(spec.key[4])/100.0, 0, 1, [], true)
		_add(preview, spec.inputs.sentinel, Vector2i(2, 8), Vector2(6, 0))
		assert(preview.diagnostic_groups.size() == 2)
		var child: Node2D = preview.diagnostic_groups[0]
		var parent: Node2D = preview.diagnostic_groups[1]
		assert(child.get_parent() == parent.get_node("Contents"))
		if args[2] == "stale":
			# Negative control: copy before the earlier middle sibling instead of
			# immediately before the child's composite. This must change pixels.
			var composite := child.get_node("Composite")
			var copy := composite.get_node("DestinationCopy")
			composite.remove_child(copy)
			copy.set_meta("blend_source_transform", Transform2D.IDENTITY)
			parent.get_node("Contents").add_child(copy)
			parent.get_node("Contents").move_child(copy, 0)
		view.add_child(preview)
		views.append(view)
		groups.append([child, parent])
	for tick in 12:
		await process_frame
		await RenderingServer.frame_post_draw
	var atlases := {"child": Image.create(8, 432*8, false, Image.FORMAT_RGBA8),
		"parent": Image.create(12, 432*8, false, Image.FORMAT_RGBA8),
		"final": Image.create(16, 432*8, false, Image.FORMAT_RGBA8)}
	for i in views.size():
		var sizes: Array = []
		var origins: Array = []
		for j in 2:
			var group: Node2D = groups[i][j]
			assert(group.get_script().resource_path == "res://blend_group.gd")
			var contents: SubViewport = group.get_node("Contents")
			var image := contents.get_texture().get_image()
			var stage := "child" if j == 0 else "parent"
			assert(image.get_size() == Vector2i(8 if j == 0 else 12, 8))
			atlases[stage].blit_rect(image, Rect2i(Vector2i.ZERO, image.get_size()), Vector2i(0, i*8))
			sizes.append([image.get_width(), image.get_height()])
			var origin: Vector2 = group.global_transform * group.get_node("Composite").position
			origins.append([origin.x, origin.y])
		var image := views[i].get_texture().get_image()
		atlases.final.blit_rect(image, Rect2i(0, 0, 16, 8), Vector2i(0, i*8))
		records.append({"case": i, "sizes": sizes, "origins": origins,
			"production_admitted": false, "copy_order": args[2]})
	for stage in atlases:
		assert(atlases[stage].save_png(args[1].path_join(stage+".png")) == OK)
	FileAccess.open(args[1].path_join("buffers.json"), FileAccess.WRITE).store_string(JSON.stringify(records, "\t")+"\n")
	print("NESTED_BUFFER_DIAGNOSTIC_OK cases=432 order="+args[2])
	quit(0)
