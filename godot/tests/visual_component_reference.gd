extends SceneTree

var cases: Array
var previews: Array = []
var views: Array = []
var clocks: Array = []
var destination: String

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	cases = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	destination = args[1]
	DirAccess.make_dir_recursive_absolute(destination)
	for spec: Dictionary in cases:
		var samples: Array[int] = []
		for value in spec.samples:
			samples.append(int(value))
		spec.samples = samples
		var view := SubViewport.new()
		view.size = Vector2i(600, 400)
		view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(view)
		var background := ColorRect.new()
		background.color = Color.html("606060")
		background.size = Vector2(600,400)
		view.add_child(background)
		var preview := TimelinePreview.new()
		preview.autoplay = false
		preview.play_timeline_sounds = false
		preview.show_collision_shapes = false
		preview.independent_visual_clock = true
		view.add_child(preview)
		preview.fighter_directory = "res://" + str(spec.timeline).trim_prefix("godot/").get_base_dir()
		preview._load_data()
		preview._timeline.wrapper = {}
		var placement: Dictionary = spec.placement.duplicate(true)
		preview._frames = {1: {"display_list": [placement]}, 2: {"display_list": [placement]}}
		preview.position = Vector2(spec.normalization.x, spec.normalization.y)
		preview.scale = Vector2.ONE * float(spec.normalization.scale)
		preview.play_source_frame(1)
		views.append(view)
		previews.append(preview)
	for tick in 101:
		for index in cases.size():
			var preview: TimelinePreview = previews[index]
			if tick > 0:
				preview.advance_retained_visual_clips()
			if tick == 10 or tick == 20:
				preview.play_source_frame(2 if tick == 10 else 1)
			else:
				preview.refresh_display()
			clocks.append({"tick": tick, "path": cases[index].id, "frame": preview.current_source_frame()})
			_collect_clocks(preview._retained_visual_clips, str(cases[index].id), tick)
		await process_frame
		await RenderingServer.frame_post_draw
		for index in cases.size():
			if tick in cases[index].samples:
				var path := destination.path_join("%s-%03d.png" % [cases[index].id, tick])
				assert(views[index].get_texture().get_image().save_png(path) == OK)
	FileAccess.open(destination.path_join("clocks.json"), FileAccess.WRITE).store_string(JSON.stringify(clocks))
	print("VISUAL_COMPONENT_REFERENCE_OK ", cases.size())
	quit()

func _collect_clocks(children: Dictionary, parent: String, tick: int) -> void:
	for depth in children:
		var clip: Dictionary = children[depth]
		var path := parent + "/" + str(depth)
		clocks.append({"tick": tick, "path": path, "frame": int(clip.frame)})
		_collect_clocks(clip.children, path, tick)
