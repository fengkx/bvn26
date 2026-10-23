extends SceneTree
const Fixture = preload("res://tests/rollback_fixture.gd")
var profile: Dictionary
var passed := 0
var root_shake_matches := false
var observed_root_y: Variant
var candidate_root := ""


func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--candidate-root="):
			candidate_root = argument.trim_prefix("--candidate-root=")
	if candidate_root.is_empty():
		push_error("Pass --candidate-root=<directory> with source-built yihu-1/2/3 profiles")
		quit(1)
		return
	_run.call_deferred()


func replace(game: Node) -> void:
	var fighter: FighterRuntime = game.naruto
	var driver: AiCpuDriver = game.player_body_driver._driver
	fighter.source_goto_frame(int(profile.source_frame), true)
	driver.run_target_frames()
	assert(not fighter.source_body_available and fighter.source_parent_frame == int(profile.parent_frame))
	driver.prepare_display_tick(int(profile.get("tick", 1)))
	driver.advance_timeline()
	driver.run_target_frames()
	assert(fighter.current_source_frame() == int(profile.next_frame) and int(fighter._timeline.sprite_id) == int(profile.target_sprite))
	assert(fighter.health == 671 and fighter.energy == 234)


func _run() -> void:
	profile = {"id": "yihu", "name": "一护", "source_frame": 1052, "source_sprite": 638, "target_sprite": 1180, "next_frame": 872, "parent_frame": 2}
	await _case()
	assert(passed == 1, "Incomplete graph fixture")
	print("YIHU_FORM_GRAPH_BODY_OK 2/2 edges; transfer, live refs, timer and rollback")
	if not root_shake_matches:
		push_error("YIHU_FORM_NATIVE_FAIL: sprite1027/frame1 root Y expected12, observed" + str(observed_root_y))
		quit(1)
		return
	print("YIHU_FORM_GRAPH_NATIVE_OK 2/2 edges and root shake")
	quit()



func _case() -> void:
	var fixture := Fixture.create(self, [profile.name, "一护"], ["鼬", "魂"])
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
	var candidate := candidate_root.path_join("yihu-1")
	var target := candidate_root.path_join("yihu-2")
	var third := candidate_root.path_join("yihu-3")
	var second_model: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(target.path_join("ai.json")))
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
	player.configure_forms({"2": {"directory": target, "load_declarations": model.frame_calls[str(profile.source_frame)][0].replacement.load_declarations}, "3": {"directory": third, "load_declarations": second_model.frame_calls["1036"][0].replacement.load_declarations}}, intervals, root_values)
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
	assert(fighter.fighter_directory == "res://generated/fighters/" + str(profile.id))
	assert(int(fighter._timeline.sprite_id) == int(profile.source_sprite) and fighter._frames.has(int(profile.source_frame)))
	assert(fighter.source_parent_frame == 1 and fighter.source_body_available)
	assert(fighter.ai_source_state.read_field("__sentinel") == 73 and fighter.ai_source_state.read_field("khit") == 91)
	assert(not game.player_body_driver._driver.source_form_context.root_intervals.handles.has("feiint"))
	replace(game)
	assert(game.player_body_driver.body == fighter.source_body)
	assert(fighter.ai_source_state.read_field("__sentinel") == null and fighter.ai_source_state.read_field("khit") == 0)
	problem = fixture.battle.load_state(after)
	assert(problem.is_empty(), problem)
	fighter = game.naruto
	assert(fighter.current_source_frame() == int(profile.next_frame) and int(fighter._timeline.sprite_id) == int(profile.target_sprite))
	var restored: SourceRootIntervals = game.player_body_driver._driver.source_form_context.root_intervals
	assert(restored.handles.has("feiint"))
	fighter.root_zhanting = false
	fighter.ai_source_state.values.wudi = false
	assert(restored.fire_recorded(int(restored.handles.feiint)))
	assert(fighter.health == 661)
	observed_root_y = game.player_body_driver._driver.source_form_context.root_values.root_y
	root_shake_matches = observed_root_y == 12
	print("YIHU_ROOT_SHAKE_OBSERVATION native=12 runtime=", observed_root_y)
	# A new source helper input: compare parent2->3 against the independent
	# original native capture, which starts with HP671/QL234 and rootY17.
	fighter.root_zhanting = true
	fighter.health = 671
	fighter.energy = 234
	game.player_body_driver._driver.source_form_context.root_values.root_y = 17
	profile = {"source_frame": 1036, "target_sprite": 1672, "next_frame": 1004, "parent_frame": 3, "tick": 2}
	var second_before: Dictionary = fixture.battle.save_state()
	assert(not second_before.has("error"), str(second_before))
	replace(game)
	assert(fighter.source_parent_frame == 3 and fighter.ai_source_state.read_field("khit") == 0)
	var third_after: Dictionary = fixture.battle.save_state()
	assert(not third_after.has("error"), str(third_after))
	problem = fixture.battle.load_state(second_before)
	assert(problem.is_empty(), problem)
	assert(game.naruto.source_parent_frame == 2 and int(game.naruto._timeline.sprite_id) == 1180)
	replace(game)
	problem = fixture.battle.load_state(third_after)
	assert(problem.is_empty(), problem)
	assert(game.naruto.source_parent_frame == 3 and int(game.naruto._timeline.sprite_id) == 1672)

	restored.clear()
	passed += 1
	print("YIHU_FORM_CASE_BODY_OK")
	Fixture.dispose(game, fixture.battle)
	await process_frame
