extends SceneTree
const Fixture = preload("res://tests/rollback_fixture.gd")
const State = preload("res://simulation_state.gd")

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var fixture := Fixture.create(self)
	var game: Node = fixture.game
	var battle: RefCounted = fixture.battle
	var initial: Dictionary = battle.save_state()
	assert(not initial.has("error"), str(initial))
	for corruption in ["frame", "build", "graph", "graph_type"]:
		var broken := initial.duplicate(true)
		match corruption:
			"frame": broken.frame += 1
			"build": broken.build = "other-build"
			"graph": broken.owners.battle.owners.graph += "00"
			"graph_type": broken.owners.battle.owners.graph = null
		assert(not battle.load_state(broken).is_empty())
		assert(State.first_difference(initial, battle.save_state()).is_empty())
	var scale_before: Vector2 = game.ichigo.scale
	game.ichigo.position.x += 200
	game.ichigo.scale = Vector2(3, 4)
	game.naruto.health -= 123
	game.source_random.next_value("rollback-test")
	assert(battle.load_state(initial).is_empty())
	assert(game.ichigo.scale == scale_before)
	assert(State.first_difference(initial, battle.save_state()).is_empty())
	var queue: AiSourceTimeouts = game.player_body_driver._driver.timeouts
	var timeout_id := queue.schedule(game.player_body_driver.body.updateDirect, 10)
	var pending: Dictionary = battle.save_state()
	var players := {"p1": {}, "p2": {}}
	for slot in players:
		for button in preload("res://rollback_session.gd").BUTTONS: players[slot][button] = false
	assert(battle.set_frame_events(1, 33, false, [{"kind": "body_timeout", "phase": "after_actor_advance", "slot": "p1", "id": timeout_id}]).is_empty())
	assert(battle.advance(1, players).is_empty())
	assert(queue.pending_count() == 0)
	var delivered: Dictionary = battle.save_state()
	assert(battle.load_state(pending).is_empty())
	assert(queue.pending_count() == 1)
	assert(battle.advance(1, players).is_empty())
	assert(queue.pending_count() == 0)
	assert(State.first_difference(delivered, battle.save_state()).is_empty())
	game.naruto.goto_ai_label("走", false)
	game._fighter_visual_service(game.naruto, "showdow", [{"R": 20, "G": -100, "B": 255}])
	var shadows: Array = game.game_world.get_children().filter(func(node): return node is ShadowSnapshot)
	assert(shadows.size() == 1)
	var shadow: ShadowSnapshot = shadows[0]
	var frozen: Dictionary = battle.save_state()
	assert(not frozen.has("error"), str(frozen))
	for index in 10: shadow.fade()
	assert(shadow.get_parent() == null and is_instance_valid(shadow))
	assert(battle.load_state(frozen).is_empty())
	assert(shadow.get_parent() == game.game_world)
	assert(shadow.capture_viewport.get_child(0).get_child_count() > 0)
	assert(State.first_difference(frozen, battle.save_state()).is_empty())
	var sound_file := ""
	for asset in game.naruto._assets.values():
		if str(asset).ends_with(".mp3") or str(asset).ends_with(".wav"):
			sound_file = str(asset)
			break
	assert(not sound_file.is_empty())
	var published: int = battle.checkpoint.published_sounds
	var suppressed: int = battle.checkpoint.suppressed_sounds
	assert(game.naruto._start_sound_player({}, sound_file, true, "nested:A"))
	assert(game.naruto._start_sound_player({}, sound_file, true, "nested:B"))
	assert(game.naruto._start_sound_player({}, sound_file, true, "nested:A"))
	assert(battle.checkpoint.published_sounds == published + 2)
	assert(battle.checkpoint.suppressed_sounds == suppressed + 1)
	Fixture.dispose(game, battle)
	await process_frame
	print("BATTLE_CHECKPOINT_SMOKE_OK rejects=4 restores_negative_scale_rng_health_shadow_timeout=true")
	quit()
