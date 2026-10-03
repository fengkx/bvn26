extends SceneTree

const Battle = preload("res://rollback_battle.gd")
const Inputs = preload("res://rollback_test_session.gd")
const State = preload("res://simulation_state.gd")

func _decode_graph(graph: Variant) -> Array:
	var graph_bytes: PackedByteArray = graph.hex_decode() if graph is String else graph
	return bytes_to_var(graph_bytes)

func _initialize() -> void:
	_run.call_deferred()

func _players(frame: int) -> Dictionary:
	var players := {"p1": {}, "p2": {}}
	for slot in players:
		for button in Inputs.BUTTONS: players[slot][button] = false
	if frame >= 145 and frame < 170:
		players.p1.right = true
		players.p2.left = true
	var phase := (frame - 170) % 120
	if frame >= 170:
		for slot in players:
			players[slot].attack = phase >= 0 and phase < 3
			players[slot].ranged = phase >= 24 and phase < 27
			players[slot].summon = phase >= 48 and phase < 51
			players[slot].special = phase >= 80 and phase < 83
			players[slot].down = phase >= 80 and phase < 83
	return players

func _run() -> void:
	var roster: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/character_selection/available.json"))
	var stages: Array = JSON.parse_string(FileAccess.get_file_as_string("res://generated/stages/catalog/catalog.json")).stages
	var names: Array = roster.fighters.keys()
	var helpers: Array = roster.helpers.keys()
	for index in names.size():
		var fixture := preload("res://tests/rollback_fixture.gd").create(self,
			[names[index], names[(index + 1) % names.size()]],
			[helpers[index % helpers.size()], helpers[(index + 1) % helpers.size()]],
			stages[index % stages.size()].id)
		var game: Node = fixture.game
		var battle: RefCounted = fixture.battle
		game.naruto.energy = 300
		game.ichigo.energy = 300
		var checkpoints := {}
		for frame in range(1, 341):
			var skip := frame >= 30 and frame < 90
			var callbacks := []
			if game.battle_intro.polling and frame % 15 == 0 and not (skip and game.battle_intro.step > 1 and game.battle_intro.step < 4):
				callbacks.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": frame, "time_ms": frame * 33})
			assert(battle.set_frame_events(frame, frame * 33, skip, callbacks).is_empty())
			var problem: String = battle.advance(frame, _players(frame))
			assert(problem.is_empty(), problem)
			if frame in [168, 177, 201, 225, 253, 285, 310, 340]:
				checkpoints[frame] = battle.save_state()
				assert(not checkpoints[frame].has("error"), str(checkpoints[frame]))
			if frame % 60 == 0: await process_frame
		var boundaries := checkpoints.keys()
		for position in range(boundaries.size() - 1):
			var first: int = boundaries[position]
			var last: int = boundaries[position + 1]
			battle.begin_replay()
			var problem: String = battle.load_state(checkpoints[first])
			assert(problem.is_empty(), problem)
			for frame in range(first + 1, last + 1):
				problem = battle.advance(frame, _players(frame))
				assert(problem.is_empty(), problem)
			battle.end_replay()
			assert(battle.checkpoint._pending_displays.is_empty())
			var restored: Dictionary = battle.save_state()
			var difference := State.first_difference(checkpoints[last], restored)
			if not difference.is_empty():
				FileAccess.open("/tmp/roster-expected.json", FileAccess.WRITE).store_string(JSON.stringify(_decode_graph(checkpoints[last].owners.battle.owners.graph), "  "))
				FileAccess.open("/tmp/roster-actual.json", FileAccess.WRITE).store_string(JSON.stringify(_decode_graph(restored.owners.battle.owners.graph), "  "))
			assert(difference.is_empty(), "%s %d..%d: %s" % [names[index], first, last, difference])
		print("ROLLBACK_ROSTER_CASE_OK fighter=%s helper=%s map=%s checkpoints=%d" % [names[index], helpers[index % helpers.size()], stages[index % stages.size()].id, boundaries.size()])
		preload("res://tests/rollback_fixture.gd").dispose(game, battle)
		await process_frame
	print("ROLLBACK_ROSTER_SMOKE_OK fighters=11 helpers=4 maps=10")
	quit()
