extends SceneTree
const Fixture = preload("res://tests/rollback_fixture.gd")


func _initialize() -> void:
	_run.call_deferred()


func replace(game: Node) -> void:
	var fighter: FighterRuntime = game.naruto
	var driver: AiCpuDriver = game.player_body_driver._driver
	fighter.source_goto_frame(1148, true)
	driver.run_target_frames()
	assert(not fighter.source_body_available and fighter.source_parent_frame == 2)
	driver.prepare_display_tick(1)
	driver.advance_timeline()
	driver.run_target_frames()
	assert(fighter.current_source_frame() == 968 and int(fighter._timeline.sprite_id) == 808)
	assert(fighter.health == 671 and fighter.energy == 234)


func _run() -> void:
	var fixture := Fixture.create(self, ["小乌", "一护"], ["鼬", "魂"])
	var game: Node = fixture.game
	var fighter: FighterRuntime = game.naruto
	var player = game.player_body_driver
	var original_driver: AiCpuDriver = player._driver
	var platforms := original_driver.body_context.source_platforms.duplicate()
	var floor_y := original_driver.body_context.floor_y
	var map_width := original_driver.body_context.map_size_x
	var services := original_driver.services
	player.stop()
	await process_frame
	var candidate := "res://generated/fighters/weqal"
	var target := "res://generated/forms/weqal-2"
	var model: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(candidate.path_join("ai.json")))
	fighter.ai_source_state.configure(model)
	fighter.ai_source_state.apply_load()
	fighter.ai_source_state.apply_frame(1)
	fighter.ai_source_state.values.pn = 2
	fighter.source_parent_values = model.parent_initial_values.duplicate(true)
	player.configure(fighter, candidate.path_join("player_controller"), platforms, floor_y, map_width, services, game.source_callbacks)
	player._driver.timeouts.recorded = true
	var intervals := SourceRootIntervals.new()
	intervals.recorded = true
	game.add_child(intervals)
	var root_values := {"root_y": 17, "maxhp": 1000, "difficulty": 3, "helper_power:p1": null, "helper_power:p2": null}
	var keys := ["w", "s", "a", "d", "j", "k", "l", "u", "i", "o", "上箭", "下箭", "左箭", "右箭", "N1", "N2", "N3", "N4", "N5", "N6"]
	for index in keys.size(): root_values["key:" + keys[index]] = 91 + index
	player.configure_forms({"2": {"directory": target, "load_declarations": model.frame_calls["1148"][0].replacement.load_declarations}}, intervals, root_values)
	fighter.root_zhanting = true
	fighter.health = 671
	fighter.energy = 234
	fighter.ai_source_state.values.wudi = false
	fighter.ai_source_state.values.__sentinel = 73
	fighter.ai_source_state.values.khit = 91
	var before: Dictionary = fixture.battle.save_state()
	assert(not before.has("error"), str(before))
	replace(game)
	var after: Dictionary = fixture.battle.save_state()
	assert(not after.has("error"), str(after))
	var problem: String = fixture.battle.load_state(before)
	assert(problem.is_empty(), problem)
	fighter = game.naruto
	assert(fighter.fighter_directory == "res://generated/fighters/weqal")
	assert(int(fighter._timeline.sprite_id) == 387 and fighter._frames.has(1148))
	assert(fighter.source_parent_frame == 1 and fighter.source_body_available)
	assert(fighter.ai_source_state.read_field("__sentinel") == 73 and fighter.ai_source_state.read_field("khit") == 91)
	assert(not game.player_body_driver._driver.source_form_context.root_intervals.handles.has("feiint"))
	replace(game)
	assert(game.player_body_driver.body == fighter.source_body)
	assert(fighter.ai_source_state.read_field("__sentinel") == null and fighter.ai_source_state.read_field("khit") == 0)
	problem = fixture.battle.load_state(after)
	assert(problem.is_empty(), problem)
	fighter = game.naruto
	assert(fighter.current_source_frame() == 968 and int(fighter._timeline.sprite_id) == 808)
	var restored: SourceRootIntervals = game.player_body_driver._driver.source_form_context.root_intervals
	assert(restored.handles.has("feiint"))
	fighter.root_zhanting = false
	fighter.ai_source_state.values.wudi = false
	assert(restored.fire_recorded(int(restored.handles.feiint)))
	assert(fighter.health == 661)
	restored.clear()
	# Controlled source timeline entry: no key press or synthetic action finish.
	assert(fixture.battle.load_state(before).is_empty())
	fighter = game.naruto
	var driver: AiCpuDriver = game.player_body_driver._driver
	fighter.source_goto_frame(1061, true)
	driver.run_target_frames()
	var saw_fallthrough := false
	for tick in range(1, 130):
		driver.prepare_display_tick(tick)
		driver.advance_timeline()
		saw_fallthrough = saw_fallthrough or fighter.current_source_frame() == 1100
		driver.run_target_frames()
		if fighter.source_parent_frame == 2 and fighter.source_body_available:
			break
	assert(saw_fallthrough, "Source failure label must naturally reach frame 1100")
	assert(fighter.source_parent_frame == 2 and int(fighter._timeline.sprite_id) == 808)
	# The later explicit parent goto remains executable even when entered directly.
	assert(fixture.battle.load_state(before).is_empty())
	fighter = game.naruto
	driver = game.player_body_driver._driver
	fighter.source_goto_frame(1152, true)
	driver.run_target_frames()
	assert(fighter.source_parent_frame == 2 and not fighter.source_body_available)
	driver.prepare_display_tick(1)
	driver.advance_timeline()
	driver.run_target_frames()
	assert(fighter.source_body_available and int(fighter._timeline.sprite_id) == 808)
	print("WEQAL_REPLACEMENT_CHECKPOINT_OK base_restore_redo target_restore captured_root_interval_live failure_fallthrough parent_goto")
	Fixture.dispose(game, fixture.battle)
	await process_frame
	quit()
