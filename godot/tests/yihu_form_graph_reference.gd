extends SceneTree
const Fixture = preload("res://tests/rollback_fixture.gd")
var profile: Dictionary
var passed := 0
var root_shake_matches := false
var observed_root_y: Variant
func _initialize() -> void:
	_run.call_deferred()


func replace(game: Node, battle: RefCounted) -> void:
	var fighter: FighterRuntime = game.naruto
	var driver: AiCpuDriver = game.player_body_driver._driver
	fighter.source_goto_frame(int(profile.source_frame), true)
	driver.run_target_frames()
	assert(not fighter.source_body_available and fighter.source_parent_frame == int(profile.parent_frame))
	var pending: Dictionary = battle.save_state()
	assert(not pending.has("error"), str(pending))
	assert(driver.source_form_profiles.is_read_only() and driver._pending_form.is_read_only())
	driver.prepare_display_tick(int(profile.get("tick", 1)))
	driver.advance_timeline()
	driver.run_target_frames()
	assert(fighter.current_source_frame() == int(profile.next_frame) and int(fighter._timeline.sprite_id) == int(profile.target_sprite))
	assert(fighter.health == 671 and fighter.energy == 234)
	assert(battle.load_state(pending).is_empty())
	fighter = game.naruto
	driver = game.player_body_driver._driver
	assert(not fighter.source_body_available and not driver._pending_form.is_empty())
	driver.prepare_display_tick(int(profile.get("tick", 1)))
	driver.advance_timeline()
	driver.run_target_frames()
	assert(fighter.current_source_frame() == int(profile.next_frame))
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
	assert(FileAccess.file_exists(fighter.fighter_directory.path_join("form_profiles.json")))
	player._driver.timeouts.recorded = true
	var root_values: Dictionary = game.source_form_root_values
	root_values.root_y = 17
	game.position.y = 17
	fighter.root_zhanting = true
	fighter.health = 671
	fighter.energy = 234
	fighter.ai_source_state.values.wudi = false
	fighter.ai_source_state.values.__sentinel = 73
	fighter.ai_source_state.values.khit = 91
	var before: Dictionary = fixture.battle.save_state()
	assert(not before.has("error"), str(before))
	replace(game, fixture.battle)
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
	replace(game, fixture.battle)
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
	var reference: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://../tools/probes/fixtures/yihu-nested-stage.json"))
	for row: Dictionary in reference.observations:
		if int(row.tick) > 2:
			player._driver.prepare_display_tick(int(row.tick))
			player._driver.advance_timeline()
			player._driver.run_target_frames()
		assert(fighter.current_source_frame() == int(row.body_frame))
		assert(game.position.y == float(row.root_y), str(row) + " runtime=" + str(game.position.y))
		var before_refresh: Vector2 = game.position
		fighter.refresh_display()
		fighter.refresh_checkpoint_display()
		player._driver.run_target_frames()
		assert(game.position == before_refresh, "Display refresh must not replay nested stage actions")
	print("YIHU_NESTED_STAGE_NATIVE_OK 23/23 body frames and root positions; repeated render inert")
	# A new source helper input: compare parent2->3 against the independent
	# original native capture, which starts with HP671/QL234 and rootY17.
	fighter.root_zhanting = true
	fighter.health = 671
	fighter.energy = 234
	game.player_body_driver._driver.source_form_context.root_values.root_y = 17
	game.position.y = 17
	profile = {"source_frame": 1036, "target_sprite": 1672, "next_frame": 1004, "parent_frame": 3, "tick": 25}
	var second_before: Dictionary = fixture.battle.save_state()
	assert(not second_before.has("error"), str(second_before))
	replace(game, fixture.battle)
	assert(fighter.source_parent_frame == 3 and fighter.ai_source_state.read_field("khit") == 0)
	assert(game.position.y == 17, "Native third-form observation preserves root Y")
	var third_after: Dictionary = fixture.battle.save_state()
	assert(not third_after.has("error"), str(third_after))
	problem = fixture.battle.load_state(second_before)
	assert(problem.is_empty(), problem)
	assert(game.naruto.source_parent_frame == 2 and int(game.naruto._timeline.sprite_id) == 1180)
	replace(game, fixture.battle)
	problem = fixture.battle.load_state(third_after)
	assert(problem.is_empty(), problem)
	assert(game.naruto.source_parent_frame == 3 and int(game.naruto._timeline.sprite_id) == 1672)

	restored.clear()
	passed += 1
	print("YIHU_FORM_CASE_BODY_OK")
	Fixture.dispose(game, fixture.battle)
	await process_frame
