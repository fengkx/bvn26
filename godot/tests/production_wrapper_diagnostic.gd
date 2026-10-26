extends SceneTree
const Preview = preload("res://tests/production_sampler_preview.gd")

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2)
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	assert(fixture.production_admitted == false)
	var records: Array = []
	for spec: Dictionary in fixture.cases:
		var view := SubViewport.new()
		view.size = Vector2i(600, 400)
		view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(view)
		var background := ColorRect.new()
		background.color = Color.html("606060")
		background.size = Vector2(600, 400)
		view.add_child(background)
		var preview = Preview.new()
		preview.autoplay = false
		preview.play_timeline_sounds = false
		preview.show_collision_shapes = false
		preview.independent_visual_clock = true
		view.add_child(preview)
		preview.fighter_directory = "res://" + str(spec.timeline).trim_prefix("godot/").get_base_dir()
		preview._load_data()
		preview._timeline.wrapper = {}
		preview._frames = {1: {"display_list": [spec.placement.duplicate(true)]}}
		preview.position = Vector2(spec.normalization.x, spec.normalization.y)
		preview.scale = Vector2.ONE * float(spec.normalization.scale)
		preview.play_source_frame(1)
		var buffers: Array = preview.bind_allocated_buffers()
		for tick in 8:
			await process_frame
			await RenderingServer.frame_post_draw
		for sample in spec.samples:
			assert(view.get_texture().get_image().save_png(args[1].path_join("%s-%03d.png" % [spec.id, int(sample)])) == OK)
		var leaf: Sprite2D = preview.diagnostic_leaves[0]
		var contents: SubViewport = leaf.get_parent()
		var group := contents.get_parent()
		contents.get_texture().get_image().save_png(args[1].path_join(spec.id+"-input.png"))
		group.get_node("Composite").texture.get_image().save_png(args[1].path_join(spec.id+"-glow.png"))
		var texture: Texture2D = leaf.material.get_shader_parameter("source_texture")
		texture.get_image().save_png(args[1].path_join("decoded.png"))
		records.append({"case": spec.id, "buffers": buffers})
		view.queue_free()
		await process_frame
	FileAccess.open(args[1].path_join("buffers.json"), FileAccess.WRITE).store_string(JSON.stringify(records, "\t")+"\n")
	print("PRODUCTION_WRAPPER_DIAGNOSTIC_RENDER_OK cases=%d" % fixture.cases.size())
	quit(0)
