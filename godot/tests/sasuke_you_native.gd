extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var sasuke := FighterRuntime.new()
	sasuke.fighter_directory = "res://generated/fighters/sasuke"
	root.add_child(sasuke)
	await process_frame

	assert(sasuke.fighter_name == "佐助")
	for label in [
		"站立", "走", "跳", "落", "落2", "跳砍", "跳招", "砍1", "砍2", "砍3",
		"砍技1", "砍技2", "招1", "招2", "招3", "必杀", "上必杀", "超必杀", "招换",
		"防御", "防御2", "防住", "被打", "击飞", "击落地", "起身"
	]:
		assert(not sasuke.action_range(label).is_empty(), "missing Sasuke action: " + label)
	for label in ["砍1", "砍技1", "砍技2", "必杀", "上必杀", "超必杀", "招换", "防御", "跳"]:
		assert(sasuke.command_is_wired(label), "unwired Sasuke command: " + label)

	sasuke.source_x = 100.0
	sasuke.enter_frame({"right": true})
	assert(sasuke.action == "走")
	assert(sasuke.source_x == 108.0)

	sasuke.start_action("砍1")
	assert(sasuke.current_source_frame() == 203)
	sasuke.play_source_frame(220)
	sasuke.run_frame_actions()
	assert(sasuke.action == "站立")

	sasuke.energy = 100.0
	sasuke.enter_frame({"special": true})
	assert(sasuke.action == "必杀")

	var you := HelperRuntime.new()
	you.helper_directory = "res://generated/helpers/you"
	root.add_child(you)
	await process_frame
	you.activate({"x": 120.0, "y": 0.0, "facing": -1}, sasuke)
	assert(you.helper_id == "鼬")
	assert(you.attacking and you.visible and you.current_source_frame() == 2)
	for _tick in 250:
		you.enter_frame()
		you.advance_timeline()
		if not you.attacking:
			break
	assert(not you.attacking)
	assert(you.current_source_frame() == 1)

	print("SASUKE_YOU_NATIVE_OK")
	you.queue_free()
	sasuke.queue_free()
	await process_frame
	quit()
