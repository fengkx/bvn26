extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	assert(ProjectSettings.load_resource_pack(OS.get_cmdline_user_args()[0], true))
	var available: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/character_selection/available.json"))
	assert(available.fighters.size() == 34 and available.helpers.size() == 6)
	assert(available.helpers["织姬"] == "zhiji")
	var model: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/helpers/zhiji/combat.json"))
	assert(model.health_events.size() == 7)
	assert(load("res://generated/main/character_selection/footer-name-zhiji.png") != null)
	var owner = load("res://fighter_runtime.gd").new()
	owner.health = 950
	var helper = load("res://helper_runtime.gd").new()
	helper.helper_directory = "res://generated/helpers/zhiji"
	root.add_child(helper)
	helper.activate({"x": 300, "y": -25, "facing": 1}, owner)
	for tick in 91:
		helper.advance_timeline()
		helper.enter_frame()
	assert(owner.health == 1090)
	assert(not helper.attacking)
	helper.queue_free()
	owner.free()
	await process_frame
	assert(await preload("res://tests/audio_shutdown.gd").drain(self))
	print("PACKED_ZHIJI_OK fighters=34 helpers=6 health=1090")
	quit()
