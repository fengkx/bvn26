extends SceneTree

const Fixture = preload("res://tests/rollback_fixture.gd")
const BattleInputs = preload("res://rollback_session.gd")

func _initialize() -> void:
	_run.call_deferred()

func _players(frame: int) -> Dictionary:
	var result := {"p1": {}, "p2": {}}
	for slot in result:
		for button in BattleInputs.BUTTONS: result[slot][button] = false
	if frame >= 165 and frame < 190:
		result.p1.right = true
		result.p2.left = true
	if frame >= 195 and frame < 200:
		result.p1.attack = true
		result.p2.attack = true
	if frame >= 205 and frame < 207: result.p1.jump = true
	if frame >= 235 and frame < 237: result.p1.ranged = true
	if frame >= 270 and frame < 272: result.p2.summon = true
	return result

func _fail(message: String) -> void:
	push_error(message)
	quit(1)

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 1:
		_fail("Expected one checkpoint graph tape output path")
		return
	var output := FileAccess.open(args[0], FileAccess.WRITE)
	if output == null:
		_fail("Could not open checkpoint graph tape: " + args[0])
		return
	var fixture := Fixture.create(self)
	var game: Node = fixture.game
	var battle: RefCounted = fixture.battle
	for frame in range(0, 331):
		if frame > 0:
			var skip := frame >= 30 and frame < 90
			var callbacks := []
			if game.battle_intro.polling and frame % 15 == 0 and not (skip and game.battle_intro.step > 1 and game.battle_intro.step < 4):
				callbacks.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": frame, "time_ms": frame * 33})
			var problem: String = battle.set_frame_events(frame, frame * 33, skip, callbacks)
			if not problem.is_empty():
				_fixture_cleanup(output, game, battle)
				_fail(problem)
				return
			problem = battle.advance(frame, _players(frame))
			if not problem.is_empty():
				_fixture_cleanup(output, game, battle)
				_fail(problem)
				return
		var snapshot: Dictionary = battle.save_state()
		if snapshot.has("error"):
			_fixture_cleanup(output, game, battle)
			_fail(str(snapshot.error))
			return
		var graph: String = snapshot.owners.battle.owners.graph
		output.store_string("%d:%d:%s\n" % [frame, graph.length(), graph])
	output.flush()
	output.close()
	Fixture.dispose(game, battle)
	await process_frame
	print("CHECKPOINT_GRAPH_CAPTURE_OK frames=331")
	quit()

func _fixture_cleanup(output: FileAccess, game: Node, battle: RefCounted) -> void:
	output.close()
	Fixture.dispose(game, battle)
