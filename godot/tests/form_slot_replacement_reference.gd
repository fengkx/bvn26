extends SceneTree
const Fixture = preload("res://tests/rollback_fixture.gd")
var passed := 0


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	for slot in [1, 2]:
		await _case(slot)
	assert(passed == 2)
	print("FORM_SLOT_REPLACEMENT_OK 2/2 slots; native transfer/frame1017/root interval floor/pause/live refs and full rollback")
	quit()


func _case(slot: int) -> void:
	var selected := ["佐助", "一护"] if slot == 1 else ["一护", "佐助"]
	var fixture := Fixture.create(self, selected, ["鼬", "魂"])
	var game: Node = fixture.game
	var fighter: FighterRuntime = game.naruto if slot == 1 else game.ichigo
	var driver: AiCpuDriver = game.player_body_driver._driver if slot == 1 else game.opponent_driver
	var services := driver.services
	var platforms := driver.body_context.source_platforms.duplicate()
	var context: AiBodyContext = driver.body_context
	driver.stop()
	var base := "res://generated/fighters/sasuke"
	var target := "res://generated/forms/sasuke-2"
	var model: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(base.path_join("ai.json")))
	fighter.ai_source_state.configure(model)
	fighter.ai_source_state.apply_load()
	fighter.ai_source_state.apply_frame(1)
	fighter.ai_source_state.values.pn = 2 if slot == 1 else 1
	fighter.source_parent_values = model.parent_initial_values.duplicate(true)
	context.use_ai = false
	driver.configure(fighter, base.path_join("player_controller"), platforms, -25, 1000, {"touchFloor": null}, services, true, game.source_callbacks, context)
	if slot == 1: game.player_body_driver._on_body_replaced()
	driver.timeouts.recorded = true
	game.recorded_form_timers = true
	game._prepare_form_root_owner()
	game.source_root_intervals.recorded = true
	var values: Dictionary = game.source_form_root_values
	values.maxhp = 1500
	values.p1bs = "p1-original"
	values.p2bs = "p2-original"
	driver.configure_forms({"2": {"directory": target, "load_declarations": model.frame_calls["1232"][0].replacement.load_declarations}}, game.source_root_intervals, values)
	fighter.health = 671
	fighter.energy = 234
	fighter.root_zhanting = true
	fighter.ai_source_state.values.wudi = true
	var old_reference := driver.source_form_context.body_reference
	var before: Dictionary = fixture.battle.save_state()
	assert(not before.has("error"), str(before))
	fighter.source_goto_frame(1228, true)
	driver.run_target_frames()
	for tick in range(1, 5):
		driver.prepare_display_tick(tick)
		driver.advance_timeline()
		driver.run_target_frames()
	assert(not fighter.source_body_available and fighter.source_parent_frame == 2)
	assert(old_reference.read_field("hp") == null)
	assert(values["p%dbs" % slot] == "佐助咒怨")
	assert(values["p%dbs" % (3 - slot)] == "p%d-original" % (3 - slot))
	var interval_name := "feiint" if slot == 1 else "feiint2"
	assert(game.source_root_intervals.handles.has(interval_name))
	driver.prepare_display_tick(5)
	driver.advance_timeline()
	driver.run_target_frames()
	assert(fighter.current_source_frame() == 1017)
	assert(old_reference.read_field("hp") == 671 and fighter.energy == 234)
	var after: Dictionary = fixture.battle.save_state()
	assert(not after.has("error"), str(after))
	var problem: String = fixture.battle.load_state(before)
	assert(problem.is_empty(), problem)
	assert(fighter.source_parent_frame == 1 and int(fighter._timeline.sprite_id) == 603)
	assert(game.source_form_root_values["p%dbs" % slot] == "p%d-original" % slot)
	problem = fixture.battle.load_state(after)
	assert(problem.is_empty(), problem)
	assert(fighter.source_parent_frame == 2 and fighter.current_source_frame() == 1017)
	var handle := int(game.source_root_intervals.handles[interval_name])
	fighter.ai_source_state.values.wudi = true
	fighter.root_zhanting = false
	assert(game.source_root_intervals.fire_recorded(handle))
	assert(fighter.health == 661)
	fighter.health = 300
	assert(game.source_root_intervals.fire_recorded(handle))
	assert(fighter.health == 300)
	fighter.health = 301
	assert(game.source_root_intervals.fire_recorded(handle))
	assert(fighter.health == 291)
	fighter.root_zhanting = true
	assert(game.source_root_intervals.fire_recorded(handle))
	assert(fighter.health == 291)
	passed += 1
	Fixture.dispose(game, fixture.battle)
	await process_frame
