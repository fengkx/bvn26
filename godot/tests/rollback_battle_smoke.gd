extends SceneTree

const Battle = preload("res://rollback_battle.gd")
const Session = preload("res://rollback_test_session.gd")
const State = preload("res://simulation_state.gd")
var game: Node
var battle: RefCounted

func _initialize() -> void:
	_run.call_deferred()

func players(frame: int) -> Dictionary:
	var result := {"p1": {}, "p2": {}}
	for slot in result:
		for button in Session.BUTTONS: result[slot][button] = false
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

func check(problem: String) -> void:
	if not problem.is_empty():
		push_error(problem)
		quit(1)
		assert(false, problem)

func _run() -> void:
	var fixture := preload("res://tests/rollback_fixture.gd").create(self)
	game = fixture.game
	battle = fixture.battle
	var initial: Dictionary = battle.save_state()
	assert(not initial.has("error"), str(initial))
	var reference := {}
	var start := Time.get_ticks_msec()
	for frame in range(1, 331):
		var skip := frame >= 30 and frame < 90
		var callbacks := []
		if game.battle_intro.polling and frame % 15 == 0 and not (skip and game.battle_intro.step > 1 and game.battle_intro.step < 4):
			callbacks.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": frame, "time_ms": frame * 33})
		check(battle.set_frame_events(frame, frame * 33, skip, callbacks))
		check(battle.advance(frame, players(frame)))
		if frame == 330: reference = battle.save_state()
	assert(game.ichigo.health < game.session.maxhp or game.naruto.health < game.session.maxhp)
	check(battle.load_state(initial))
	var session := Session.new()
	check(session.configure(battle, "real-battle", 8, 12))
	var wall_tick := 0
	var delivered := 0
	var waits := 0
	while session.frontier < 330 or session.confirmed < 330:
		wall_tick += 1
		assert(wall_tick < 400)
		if session.frontier < 330:
			var next := session.frontier + 1
			check(session.receive("real-battle", "p1", next, players(next).p1))
		# Delay, reverse-order bursts, duplicate delivery and a temporary outage.
		if wall_tick % 3 == 0 and not (wall_tick >= 165 and wall_tick < 180):
			var through := 330 if session.frontier == 330 else maxi(0, session.frontier - 5)
			for remote_frame in range(through, delivered, -1):
				check(session.receive("real-battle", "p2", remote_frame, players(remote_frame).p2))
				check(session.receive("real-battle", "p2", remote_frame, players(remote_frame).p2))
			delivered = maxi(delivered, through)
		if session.frontier < 330:
			var previous := session.frontier
			var result := session.step()
			if result == "waiting_for_input":
				waits += 1
				assert(session.frontier == previous)
			else: check(result)
		if wall_tick % 30 == 0:
			print("ROLLBACK_BATTLE_PROGRESS frame=", session.frontier, " corrections=", session.rollback_count)
			await process_frame
	assert(waits > 0)
	var actual: Dictionary = session.state_at(330)
	var difference := State.first_difference(reference, actual)
	if not difference.is_empty():
		FileAccess.open("/tmp/rollback-battle-expected.json", FileAccess.WRITE).store_string(JSON.stringify(reference, "  "))
		FileAccess.open("/tmp/rollback-battle-actual.json", FileAccess.WRITE).store_string(JSON.stringify(actual, "  "))
	check(difference)
	assert(session.rollback_count >= 6 and session.confirmed == 330)
	print("ROLLBACK_BATTLE_SMOKE_OK frames=330 rollbacks=%d replayed=%d waits=%d elapsed_ms=%d retained_bytes=%d sounds_suppressed=%d" % [session.rollback_count, session.replayed_frames, waits, Time.get_ticks_msec() - start, session.retained_bytes(), battle.checkpoint.suppressed_sounds])
	print("ROLLBACK_PROFILE ", battle.checkpoint.profile)
	preload("res://tests/rollback_fixture.gd").dispose(game, battle)
	await process_frame
	fixture = preload("res://tests/rollback_fixture.gd").create(self)
	game = fixture.game
	battle = fixture.battle
	for frame in range(1, 331):
		var skip := frame >= 30 and frame < 90
		var callbacks := []
		if game.battle_intro.polling and frame % 15 == 0 and not (skip and game.battle_intro.step > 1 and game.battle_intro.step < 4):
			callbacks.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": frame, "time_ms": frame * 33})
		check(battle.set_frame_events(frame, frame * 33, skip, callbacks))
		check(battle.advance(frame, players(frame)))
	check(State.first_difference(reference, battle.save_state()))
	preload("res://tests/rollback_fixture.gd").dispose(game, battle)
	await process_frame
	print("ROLLBACK_INDEPENDENT_RUN_OK frames=330 full_state=true")
	quit()
