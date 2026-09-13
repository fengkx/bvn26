extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var helper := HelperRuntime.new()
	helper.helper_directory = "res://generated/helpers/jinye"
	helper.fighter_directory = helper.helper_directory
	helper.autoplay = false
	root.add_child(helper)
	await process_frame

	assert(helper.helper_id == "松本")
	assert(helper._timeline["source_swf"]["path"] == "game/fighter/fz/jinye.swf")
	assert(helper._timeline["frame_count"] == 73)
	assert(not helper._assets.is_empty())
	assert(helper._timeline["frames"][1]["frame"] == 2)

	helper.activate({"x": 240.0, "y": 0.0, "facing": -1, "start_frame": 2}, null)
	assert(helper.attacking)
	assert(helper.visible)
	assert(helper.position == Vector2(240.0, 0.0))

	for _tick in 11:
		helper.advance_timeline()
		helper.enter_frame()
	assert(helper.current_source_frame() == 13)
	assert(helper.source_action == 1)

	for _tick in 43:
		helper.advance_timeline()
		helper.enter_frame()
	assert(helper.current_source_frame() == 56)
	assert(helper.source_action == 0)

	helper.queue_free()
	await process_frame
	print("JINYE_IMPORT_SMOKE_OK")
	quit()
