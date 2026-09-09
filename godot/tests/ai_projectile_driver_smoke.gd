extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var cpu := FighterRuntime.new()
	cpu.fighter_directory = "res://generated/fighters/yihu"
	var player := FighterRuntime.new()
	player.fighter_directory = "res://generated/fighters/minren"
	root.add_child(cpu)
	root.add_child(player)
	await process_frame
	cpu.opponent = player
	player.opponent = cpu
	cpu.position = Vector2(300, 0)
	player.position = Vector2(900, 0)
	cpu.ai_source_state.apply_load()
	cpu.ai_source_state.values["_lastX"] = 300
	var frame_queue: Array[Callable] = []
	cpu.source_child_frame_requested.connect(func(operation: Callable) -> void: frame_queue.append(operation))
	var driver := AiCpuDriver.new()
	root.add_child(driver)
	driver.configure(cpu, "res://generated/fighters/yihu/ai_controller", {}, 0, 1000,
		{"touchFloor": null}, func(_name: String, _args: Array) -> Variant: return null, true)
	var profile: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://../spec/execution-profile.json"))
	# The source frame placement and its first callback dispatch share tick 1.
	driver.prepare_display_tick(1)
	cpu.start_action("招1")
	cpu.play_source_frame(327)
	cpu.run_frame_actions()
	driver.begin_display_tick(1)
	driver.run_enter_frame(profile)
	assert(cpu.instance_local_offset("zh1atm") == Vector2.ZERO)
	assert(cpu.instance_clip_frame("zh1atm") == 1)
	driver.begin_display_tick(2)
	driver.run_enter_frame(profile)
	assert(cpu.instance_local_offset("zh1atm") == Vector2(18, 0))
	assert(cpu.instance_clip_frame("zh1atm") == 1)
	# Impact is produced by the scheduled callback, after timeline advance.
	player.position += cpu.instance_global_bounds("zh1atm").get_center() - player.instance_global_bounds("bdmn").get_center()
	driver.begin_display_tick(3)
	driver.run_controllers(driver.controller.paths_by_descending_depth())
	assert(cpu.instance_clip_frame("zh1atm") == 5)
	assert(cpu.instance_local_offset("zh1atm") == Vector2(18, 0))
	assert(cpu.source_projectile_target_bounds("zh1atm").has_area())
	assert(not cpu.source_projectile_target_bounds("abcd").has_area())
	assert(frame_queue.size() == 1)
	var old_frame_script: Callable = frame_queue.pop_front()
	var retained_old_instance: RefCounted = old_frame_script.get_object()
	old_frame_script.call()
	assert(not cpu.source_projectile_target_bounds("zh1atm").has_area())
	assert(cpu.source_projectile_target_bounds("abcd").has_area())
	player.position = Vector2(900, 0)
	driver.begin_display_tick(4)
	assert(cpu.instance_clip_frame("zh1atm") == 6)
	driver.begin_display_tick(4)
	assert(cpu.instance_clip_frame("zh1atm") == 6)
	driver.run_controllers(driver.controller.paths_by_descending_depth())
	assert(cpu.instance_local_offset("zh1atm") == Vector2(18, 0))
	# A same-tick removal and re-placement creates a fresh stopped projectile.
	cpu.start_action("站立")
	driver.controller.synchronize(4)
	cpu.start_action("招1")
	cpu.play_source_frame(327)
	driver.controller.synchronize(4)
	driver.run_controllers(driver.controller.paths_by_descending_depth())
	assert(cpu.instance_local_offset("zh1atm") == Vector2.ZERO)
	assert(cpu.instance_clip_frame("zh1atm") == 1)
	assert(retained_old_instance.current_source_name() == null)
	old_frame_script.call()
	assert(cpu.source_projectile_target_bounds("zh1atm").has_area())
	assert(not cpu.source_projectile_target_bounds("abcd").has_area())
	driver.begin_display_tick(5)
	driver.run_controllers(driver.controller.paths_by_descending_depth())
	assert(cpu.instance_local_offset("zh1atm") == Vector2(18, 0))
	driver.stop()
	driver.queue_free()
	cpu.queue_free()
	player.queue_free()
	await process_frame
	print("AI_PROJECTILE_DRIVER_SMOKE_OK")
	quit()
