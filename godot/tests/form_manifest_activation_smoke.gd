extends SceneTree
const Fixture = preload("res://tests/rollback_fixture.gd")


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fixture := Fixture.create(self, ["带土", "一护"], ["鼬", "魂"])
	var game: Node = fixture.game
	var fighter: FighterRuntime = game.naruto
	var driver: AiCpuDriver = game.player_body_driver._driver
	assert(driver.source_form_context != null, "Main did not activate the shipped form manifest")
	assert(driver.source_form_context.root_intervals == game.source_root_intervals)
	assert(is_same(driver.source_form_context.root_values, game.source_form_root_values))
	assert(driver.source_form_profiles.has("2"))
	game.source_root_intervals.recorded = true
	driver.timeouts.recorded = true
	fighter.root_zhanting = true
	fighter.health = 671
	fighter.energy = 234
	fighter.source_goto_frame(1307, true)
	driver.run_target_frames()
	assert(not fighter.source_body_available and fighter.source_parent_frame == 2)
	driver.prepare_display_tick(1)
	driver.advance_timeline()
	driver.run_target_frames()
	assert(fighter.fighter_directory == "res://generated/forms/daitu-2")
	assert(fighter.current_source_frame() == 1292)
	assert(fighter.health == 671 and fighter.energy == 234)
	assert(fighter.ai_source_state.values["上"] == game.session.codes.w)
	assert(game.player_body_driver.body == fighter.source_body)
	assert(driver.source_form_context.body_reference.read_field("hp") == 671)
	print("FORM_MANIFEST_ACTIVATION_OK main_shipped_manifest real_source_wankai replacement_transfer_keys")
	Fixture.dispose(game, fixture.battle)
	await process_frame
	quit()
