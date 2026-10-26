extends SceneTree

var events: Array = []


func _initialize() -> void:
	_run.call_deferred()


func service(operation: String, arguments: Array) -> Variant:
	events.append([operation, arguments])
	return null


func _run() -> void:
	var candidate := "res://generated/fighters/daitu"
	var target := "res://generated/forms/daitu-2"
	var model: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(candidate.path_join("ai.json")))
	var requirement: Dictionary = model.frame_calls["1307"][0].replacement
	for scenario: Dictionary in [{"use_ai": null, "wankai": true}, {"use_ai": false, "wankai": true}, {"use_ai": true, "wankai": true}, {"use_ai": null, "wankai": false}]:
		var use_ai: Variant = scenario.use_ai
		var expected_frame := 1292 if scenario.wankai else 2
		var fighter := FighterRuntime.new()
		fighter.fighter_directory = "res://generated/fighters/daitu"
		fighter.player_slot = "p1"
		fighter.play_timeline_sounds = false
		var opponent := FighterRuntime.new()
		opponent.fighter_directory = "res://generated/fighters/minren"
		opponent.player_slot = "p2"
		opponent.play_timeline_sounds = false
		root.add_child(fighter)
		root.add_child(opponent)
		await process_frame
		fighter.opponent = opponent
		opponent.opponent = fighter
		fighter.ai_source_state.configure(model)
		fighter.ai_source_state.apply_load()
		fighter.ai_source_state.apply_frame(1)
		fighter.ai_source_state.values["pn"] = 2
		fighter.source_parent_values = model.get("parent_initial_values", {}).duplicate(true)
		assert(fighter.source_parent_values.has("万解"), "Base compiler must retain root flag initialization")
		var registry := SourceCallbackRegistry.new()
		var intervals := SourceRootIntervals.new()
		intervals.recorded = true
		root.add_child(intervals)
		var root_values := {"root_y": 17, "maxhp": 1000, "difficulty": 3, "helper_power:p1": null, "helper_power:p2": null}
		var keys := ["w", "s", "a", "d", "j", "k", "l", "u", "i", "o", "上箭", "下箭", "左箭", "右箭", "N1", "N2", "N3", "N4", "N5", "N6"]
		for index in keys.size():
			root_values["key:" + keys[index]] = 91 + index
		var driver := AiCpuDriver.new()
		root.add_child(driver)
		var context := AiBodyContext.new(fighter)
		context.use_ai = use_ai
		driver.configure(fighter, candidate.path_join("player_controller"), {}, -25, 1000,
			{"touchFloor": null}, service, true, registry, context)
		driver.configure_forms({"2": {"directory": target, "load_declarations": requirement.load_declarations}}, intervals, root_values)
		driver.begin_display_tick(0)
		fighter.root_zhanting = true
		fighter.health = 671
		fighter.energy = 234
		fighter.ai_source_state.values["wudi"] = true
		fighter.ai_source_state.values["khit"] = 91
		fighter.ai_source_state.values["__sentinel"] = 73
		fighter.visible = false
		fighter.scale.x = -0.75
		fighter.facing = 1
		var reference := driver.source_form_context.body_reference
		var saved := reference.capture_function("feixue")
		var old_body: RefCounted = driver.body
		var old_state: AiSourceState = fighter.ai_source_state
		var delivered := intervals.assign_interval("feiint2", saved.invoke, 1000)
		fighter.source_goto_frame(1307 if scenario.wankai else 1309, true)
		fighter._queue_source_frame(1309)
		driver.run_target_frames()
		assert(fighter.source_parent_frame == 2)
		assert(not fighter.source_body_available and fighter.source_body == null)
		assert(reference.read_field("hp") == null and reference.read_field("__sentinel") == null)
		assert(root_values.root_y == 17 and fighter._ai_pending_frames.is_empty())
		assert(registry.size() == 0, "Old body and child callback registrations survived")
		assert(intervals.pending_count() == 1, "Replacement cancelled a root-owned captured interval")
		driver.prepare_display_tick(1)
		driver.advance_timeline()
		assert(fighter.source_body_available and fighter.source_parent_frame == 2)
		assert(fighter.current_source_frame() == expected_frame)
		assert(fighter.visible)
		if scenario.wankai:
			assert(fighter.facing == -1 and fighter.scale.x == -0.75)
		assert(fighter.fighter_directory == target and int(fighter._timeline.sprite_id) == 1138)
		assert(driver.body != old_body and fighter.ai_source_state != old_state)
		assert(reference.same_path(driver.source_form_context.body_reference))
		assert(reference.read_field("__sentinel") == null)
		assert(reference.read_field("khit") == 0 and reference.read_field("spd") == 17 and reference.read_field("jumpPower") == 20)
		if scenario.wankai:
			assert(fighter.health == 671 and fighter.energy == 234)
			assert(fighter.ai_source_state.values["上"] == 91 and fighter.ai_source_state.values["换"] == 100)
		else:
			assert(reference.read_field("hp") == null and fighter.energy == 0)
			assert(not fighter.ai_source_state.values.has("上"))
			reference.write_field("hp", 671)
		reference.write_field("khit", 37)
		assert(fighter.ai_source_state.values.khit == 37)
		fighter.ai_source_state.values.khit = 41
		assert(reference.read_field("khit") == 41)
		assert(not registry._entries.is_empty())
		for entry: Dictionary in registry._entries.values():
			assert(entry.placed_tick == 1)
		registry.dispatch(1)
		fighter.root_zhanting = false
		fighter.ai_source_state.values.wudi = false
		assert(intervals.fire_recorded(delivered))
		assert(fighter.health == 661, "Saved initial function did not resolve replacement health/method")
		fighter.root_zhanting = true
		driver.run_target_frames()
		assert(fighter.current_source_frame() == expected_frame)
		assert(fighter.visible)
		if scenario.wankai:
			assert(fighter.facing == -1 and fighter.scale.x == -0.75)
		assert(fighter._ai_pending_frames.is_empty())
		if use_ai == true:
			assert(intervals.handles.has("airanset") and intervals.pending_count() == 2)
		else:
			assert(not intervals.handles.has("airanset"))
		assert(not fighter._assets.is_empty() and not fighter._combat.is_empty())
		intervals.clear()
		driver.stop()
		driver.free()
		intervals.free()
		fighter.free()
		opponent.free()
		await process_frame
	print("FORM_REPLACEMENT_REFERENCE_OK daitu 4/4 cases; source1307 wankai->1292 / source1309 goto->2, transfer/live refs/timers/callbacks")
	quit()
