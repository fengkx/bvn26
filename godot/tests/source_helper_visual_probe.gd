extends SceneTree

var failed := false


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 1, "Expected one visual probe specification JSON path")
	var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	var directory := str(spec.get("helper_directory", ""))
	var output := str(spec.get("output_directory", ""))
	assert(not directory.is_empty() and not output.is_empty())
	var timeline: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(directory.path_join("timeline.json")))
	DirAccess.make_dir_recursive_absolute(output)
	root.size = Vector2i(1280, 720)
	var viewport := SubViewport.new()
	viewport.size = root.size
	viewport.transparent_bg = false
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var helper := HelperRuntime.new()
	helper.helper_directory = directory
	helper.fighter_directory = directory
	helper.autoplay = false
	helper.play_timeline_sounds = false
	viewport.add_child(helper)
	await process_frame
	helper.activate({"x": 320.0, "y": 480.0, "facing": 1, "start_frame": 2}, null)
	var observations: Array[Dictionary] = []
	for value: Variant in spec.get("frames", []):
		var frame := int(value)
		helper.play_source_frame(frame)
		await process_frame
		await RenderingServer.frame_post_draw
		var timeline_frame: Dictionary = timeline["frames"][frame - 1]
		var image := viewport.get_texture().get_image()
		var image_path := output.path_join("frame-%d.png" % frame)
		var save_error := image.save_png(image_path) if image != null else ERR_CANT_CREATE
		if save_error != OK:
			push_error("Could not save helper key frame %d" % frame)
			failed = true
		observations.append({
			"source_frame": frame,
			"source_display_list": timeline_frame.get("display_list", []),
			"visible": helper.visible,
			"attacking": helper.attacking,
			"source_action": helper.source_action,
			"screenshot": image_path if save_error == OK else ""
		})
	var report := {
		"format": "source-helper-visual-probe-v1",
		"scope": "Native rendered snapshots for source-referenced helper frames; no Flash pixel parity claim",
		"helper_directory": directory,
		"source_swf": timeline.get("source_swf", {}),
		"observations": observations,
		"display_server": DisplayServer.get_name()
	}
	var file := FileAccess.open(output.path_join("trace.json"), FileAccess.WRITE)
	assert(file != null, "Could not write helper visual trace")	
	file.store_string(JSON.stringify(report, "  ") + "\n")
	file.close()
	helper.queue_free()
	await process_frame
	await process_frame
	print("SOURCE_HELPER_VISUAL_PROBE_%s " % ("FAILED" if failed else "PASSED") + JSON.stringify(report))
	quit(1 if failed else 0)
