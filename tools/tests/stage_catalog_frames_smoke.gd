extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(
		"res://generated/stages/catalog/catalog.json"))
	for stage: Dictionary in catalog.stages:
		var preview := TimelinePreview.new()
		preview.fighter_directory = "res://generated/stages/catalog/" + str(stage.directory)
		preview.initial_frame = int(stage.frame)
		preview.autoplay = false
		root.add_child(preview)
		await process_frame
		assert(preview.current_source_frame() == int(stage.frame))
		assert(preview._frames.size() == int(preview._timeline.frame_count))
		assert(preview._frames.has(6))
		var names := []
		for placement: Dictionary in preview._frames[int(stage.frame)].display_list:
			names.append(placement.get("name", ""))
		assert("p1" in names and "p2" in names)
		await physics_frame
		assert(preview.current_source_frame() == int(stage.frame))
		preview.queue_free()
		await process_frame
	print("STAGE_CATALOG_FRAMES_OK ", catalog.stages.size())
	quit.call_deferred()
