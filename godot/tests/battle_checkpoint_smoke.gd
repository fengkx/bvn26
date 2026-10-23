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
	var local_snapshot: Dictionary = initial.owners.battle
	var graph: PackedByteArray = local_snapshot.owners.graph
	assert(State.validate_value({"graph": graph}) != "", "Packed bytes escaped their checkpoint contract")
	assert(State.validate_value(local_snapshot).is_empty(), "Binary graph checkpoint envelope was rejected")
	assert(State.fingerprint(initial) != "", "Checkpoint bytes were not fingerprinted")
	var foreign_fixture := Fixture.create(self, ["日番谷", "恋次"], ["鼬", "魂"], "流魂街")
	assert(not foreign_fixture.battle.validate_state(initial).is_empty(), "Foreign battle checkpoint was accepted")
	Fixture.dispose(foreign_fixture.game, foreign_fixture.battle)
	await process_frame
	for corruption in ["frame", "build", "graph_byte", "graph_length", "graph_type", "version_type"]:
		var broken := initial.duplicate(true)
		match corruption:
			"frame": broken.frame += 1
			"build": broken.build = "other-build"
			"graph_byte": broken.owners.battle.owners.graph[0] ^= 1
			"graph_length": broken.owners.battle.owners.graph.append(0)
			"graph_type": broken.owners.battle.owners.graph = null
			"version_type": broken.owners.battle.version = float(State.VERSION)
		if corruption in ["graph_byte", "graph_length"]:
			assert(State.first_difference(initial, broken) != "", "Graph tampering was not visible")
			assert(State.fingerprint(initial) != State.fingerprint(broken), "Graph bytes were omitted from fingerprint")
			assert(local_snapshot.owners.graph == graph, "Packed byte copy-on-write changed the retained graph")
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
	var expired_key: String = battle.checkpoint._snapshot_key(initial.owners.battle)
	battle.retain_states([frozen])
	assert(not battle.checkpoint._snapshots.has(expired_key), "Expired node retention was not released")
	assert(not battle.checkpoint._snapshot_graphs.has(expired_key), "Expired graph retention was not released")
	assert(not battle.load_state(initial).is_empty(), "Expired checkpoint was accepted")
	# Release the two deliberately started MP3 playbacks before quitting the fixture.
	for player in game.find_children("*", "AudioStreamPlayer", true, false):
		player.stop()
		player.stream = null
	await process_frame
	Fixture.dispose(game, battle)
	await process_frame
	print("BATTLE_CHECKPOINT_SMOKE_OK rejects=frame_build_graph_byte_graph_length_graph_type_version_foreign_expired cow=true raw_bytes=true")
	quit()
