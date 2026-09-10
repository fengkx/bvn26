extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var kakashi := FighterRuntime.new()
	kakashi.fighter_directory = "res://generated/fighters/kakashi"
	var opponent := FighterRuntime.new()
	opponent.fighter_directory = "res://generated/fighters/yihu"
	root.add_child(kakashi)
	root.add_child(opponent)
	await process_frame
	kakashi.opponent = opponent
	opponent.opponent = kakashi
	kakashi.position = Vector2(400, 0)
	opponent.position = Vector2(400, 0)

	# Source frame 864 declares the per-instance callback flag and frame 900
	# consumes it as a conditional timeline jump.
	kakashi.ai_source_state.apply_frame(864)
	assert(kakashi.ai_source_state.read_field("Cbshit") == false)
	var branch: Dictionary = kakashi.ai_source_state.spec["frame_calls"]["900"][0]
	kakashi.ai_source_state.values["Cbshit"] = true
	var driver := AiCpuDriver.new()
	root.add_child(driver)
	# Main's P2 CPU uses the generated player_controller with use_ai enabled.
	driver.configure(kakashi, "res://generated/fighters/kakashi/player_controller", {}, 0, 1000,
		{"touchFloor": null}, func(_name: String, _args: Array) -> Variant: return null, true)
	assert(driver.controller.context.use_ai == true)
	kakashi.play_source_frame(900)
	driver._frame_service(branch)
	assert(kakashi.current_source_frame() == 921)
	kakashi.ai_source_state.apply_frame(864)
	assert(kakashi.ai_source_state.read_field("Cbshit") == false)

	# Frame 887's child callback writes the owner only after a hit and sends
	# the opponent to 被打 only while its source action is 2.
	kakashi.start_action("超必杀")
	kakashi.play_source_frame(887)
	kakashi.refresh_display()
	opponent.play_source_frame(1)
	opponent.refresh_display()
	opponent.ai_source_state.values["动作"] = 2
	var projectile: Dictionary = {}
	for item: Dictionary in kakashi._combat["projectiles"]:
		if int(item["start_frame"]) == 887:
			projectile = item
			break
	assert(not projectile.is_empty())
	kakashi.ai_source_state.values["Cbshit"] = false
	assert(not kakashi.run_projectile_callback(projectile),
		"Hit-only callback must not be treated as a child timeline jump")
	assert(kakashi.ai_source_state.read_field("Cbshit") == true)
	assert(opponent.action == "被打")
	opponent.start_action("站立")
	opponent.ai_source_state.values["动作"] = 0
	kakashi.ai_source_state.values["Cbshit"] = false
	assert(not kakashi.run_projectile_callback(projectile),
		"Hit-only callback must keep natural child timeline advancement")
	assert(kakashi.ai_source_state.read_field("Cbshit") == true)
	assert(opponent.action == "站立")

	driver.stop()
	driver.queue_free()
	kakashi.queue_free()
	opponent.queue_free()
	await process_frame
	print("KAKASHI_PROJECTILE_SEMANTICS_OK")
	quit()
