extends SceneTree
const Fixture = preload("res://tests/rollback_fixture.gd")

func _initialize() -> void:
	_run.call_deferred()

func _replace(game: Node, source_frame: int, target_sprite: int, target_frame: int, tick: int) -> void:
	var fighter: FighterRuntime = game.naruto
	var driver: AiCpuDriver = game.player_body_driver._driver
	fighter.source_goto_frame(source_frame, true)
	driver.run_target_frames()
	assert(not fighter.source_body_available)
	driver.prepare_display_tick(tick)
	driver.advance_timeline()
	driver.run_target_frames()
	assert(fighter.source_body_available)
	assert(int(fighter._timeline.sprite_id) == target_sprite)
	assert(fighter.current_source_frame() == target_frame, "Observed replacement frame: %d; expected: %d" % [fighter.current_source_frame(), target_frame])

func _run() -> void:
	var fixture := _candidate_fixture()
	var game: Node = fixture.game
	game.source_root_intervals.recorded = true
	# Original transform capture observes body frame 1515 at tick 28, after replacement initialization.
	for edge in [{"source": 1294, "sprite": 1172, "frame": 1515, "tick": 1}]:
		var fighter: FighterRuntime = game.naruto
		fighter.health = 671
		fighter.energy = 234
		fighter.ai_source_state.values.wudi = false
		fighter.ai_source_state.values.__sentinel = 73
		var before: Dictionary = fixture.battle.save_state()
		assert(not before.has("error"), str(before))
		_replace(game, edge.source, edge.sprite, edge.frame, edge.tick)
		assert(game.naruto.health == 671 and game.naruto.energy == 234)
		assert(game.naruto.ai_source_state.read_field("__sentinel") == null)
		var after: Dictionary = fixture.battle.save_state()
		assert(not after.has("error"), str(after))
		assert(fixture.battle.load_state(before).is_empty())
		assert(game.naruto.ai_source_state.read_field("__sentinel") == 73)
		_replace(game, edge.source, edge.sprite, edge.frame, edge.tick)
		assert(fixture.battle.load_state(after).is_empty())
		var timers: SourceRootIntervals = game.source_root_intervals
		assert(int(timers.handles.feiint) == edge.tick)
		game.naruto.root_zhanting = true
		assert(timers.fire_recorded(edge.tick))
		assert(game.naruto.health == 671)
		game.naruto.root_zhanting = false
		assert(timers.fire_recorded(edge.tick))
		assert(game.naruto.health == 661)
		game.naruto.health = 201
		assert(timers.fire_recorded(edge.tick))
		assert(game.naruto.health == 191)
		assert(timers.fire_recorded(edge.tick))
		assert(game.naruto.health == 191)
		print("MINRENX_FORM_EDGE_OK ", edge.sprite)
	# Source nextfight/chushi restores health and standing on the current BODY.
	game.naruto.sw = true
	game.naruto.health = 0
	game.ko_timeline.controller.nextfight()
	assert(game.naruto.health == game.session.maxhp and not game.naruto.sw)
	assert(game.naruto.current_source_frame() == 1 and game.naruto.source_parent_frame == 2)
	assert(int(game.naruto._timeline.sprite_id) == 1172)
	Fixture.dispose(game, fixture.battle)
	await process_frame
	print("MINRENX_FORM_LIFECYCLE_OK 1 edge; transfer, local reset, pause, threshold, next round and rollback")
	quit()

# Diagnostic-only registration, matching the existing move-case candidate route.
# Shared selection/catalog files remain pending serial integration.
func _candidate_fixture() -> Dictionary:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.set_process(false)
	var directory := "res://generated/fighters/minrenx"
	var fighter: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(directory.path_join("fighter.json")))
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://../manifest.json"))
	assert(fighter.fighter_id == "仙鸣" and int(fighter.form_frame) == 1)
	assert(fighter.source.swf_path == "game/fighter/minrenx.swf")
	assert(fighter.source.swf_sha256 == manifest.file_sha256[fighter.source.swf_path])
	assert(FileAccess.get_sha256("res://../" + str(fighter.source.swf_path)) == fighter.source.swf_sha256)
	for name in ["timeline.json", "combat.json", "assets.json", "ai.json", "form_profiles.json", "intro.json"]:
		assert(FileAccess.file_exists(directory.path_join(name)))
	var intro: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(directory.path_join("intro.json")))
	assert(int(intro.source_sprite_id) == 449 and intro.fighter_id == "minrenx")
	assert(not game.character_selection.available.fighters.has("仙鸣") or game.character_selection.available.fighters["仙鸣"] == "minrenx")
	game.character_selection.available.fighters["仙鸣"] = "minrenx"
	game.battle_intro.spec.fighters["minrenx"] = {"state_frames": intro.state_frames}
	game.ko_recorded_timers = true
	game.recorded_training_timers = true
	game.recorded_form_timers = true
	game.source_random.use_seed(727)
	game.source_clock.use_explicit_time(0)
	game._replace_selected_actors(["仙鸣", "一护"], ["我爱罗", "魂"])
	game._load_selected_stage("现世")
	game._enter_current_fight(3)
	game.battle_intro.recorded_polling = true
	for timer in game.title_menu.find_children("*", "Timer", true, false): timer.stop()
	var battle := preload("res://rollback_battle.gd").new()
	assert(battle.configure(game).is_empty())
	return {"game": game, "battle": battle}
