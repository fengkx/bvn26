extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fighter_script = load("res://fighter_runtime.gd")
	var renji: FighterRuntime = fighter_script.new()
	renji.fighter_directory = "res://generated/fighters/renji"
	root.add_child(renji)
	await process_frame

	assert(renji.fighter_name == "恋次")
	assert(renji.current_source_frame() == 1)
	assert(renji.has_command("砍1"))
	assert(renji.has_command("必杀"))
	assert(renji.has_command("上必杀"))
	assert(renji.has_command("超必杀"))
	assert(renji.has_command("招换"))
	assert(renji.command_is_wired("砍1"))
	assert(renji.command_is_wired("必杀"))

	renji.position = Vector2(100.0, 0.0)
	renji.enter_frame({"right": true})
	assert(renji.action == "走")
	assert(renji.position.x == 108.0)
	assert(renji.current_source_frame() == 10)

	renji.start_action("站立")
	renji.enter_frame({"jump": true})
	assert(renji.action == "跳")
	assert(renji.airborne)

	renji.start_action("站立")
	renji.airborne = false
	renji.energy = 100.0
	renji.enter_frame({"special": true})
	assert(renji.action == "必杀")
	renji.advance_timeline()
	renji.run_frame_actions()
	assert(renji.energy == 0.0)

	renji.start_action("站立")
	renji.energy = 100.0
	renji.enter_frame({"up": true, "special": true})
	assert(renji.action == "上必杀")

	print("RENJI_IMPORT_SMOKE_OK")
	quit()
