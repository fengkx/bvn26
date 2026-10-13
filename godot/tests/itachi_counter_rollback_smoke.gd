extends SceneTree

const Fixture = preload("res://tests/rollback_fixture.gd")
const Inputs = preload("res://rollback_test_session.gd")
const State = preload("res://simulation_state.gd")


func _initialize() -> void:
	_run.call_deferred()


func _players(frame: int, attack_start: int) -> Dictionary:
	var players := {"p1": {}, "p2": {}}
	for slot in players:
		for button in Inputs.BUTTONS:
			players[slot][button] = false
	players.p1.down = attack_start > 0 and frame >= attack_start and frame <= attack_start + 30
	players.p1.ranged = players.p1.down
	players.p2.attack = attack_start > 0 and frame >= attack_start + 8 and frame <= attack_start + 11
	return players


func _run() -> void:
	var fixture := Fixture.create(self, ["鼬", "一护"], ["我爱罗", "魂"], "现世")
	var game: Node = fixture.game
	var battle: RefCounted = fixture.battle
	game.naruto.energy = 300
	var initial: Dictionary = battle.save_state()
	var paused := false
	var checkpoint := {}
	var replay_start := 0
	var attack_start := -1
	var final_frame := 0
	for frame in range(1, 601):
		if not game.battle_intro.active and attack_start < 0:
			attack_start = frame
			game.naruto.source_x = 300
			game.ichigo.source_x = 350
		var callbacks := []
		if game.battle_intro.polling and frame % 15 == 0:
			callbacks.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": frame, "time_ms": frame * 33})
		assert(battle.set_frame_events(frame, frame * 33, false, callbacks).is_empty())
		assert(battle.advance(frame, _players(frame, attack_start)).is_empty())
		if attack_start > 0 and game.naruto.current_source_frame() == 449 and checkpoint.is_empty():
			assert(game.naruto.action == "招2")
			checkpoint = battle.save_state()
			replay_start = frame
			paused = true
		if frame % 60 == 0:
			await process_frame
		if attack_start > 0 and frame == attack_start + 170:
			final_frame = frame
			break
	assert(paused and final_frame > 0 and not game.battle_intro.active)
	assert(game.naruto.action == "站立")
	assert(game.ichigo.health < game.session.maxhp, "Source counter must hit the opponent")
	var expected: Dictionary = battle.save_state()
	battle.begin_replay()
	assert(battle.load_state(checkpoint).is_empty())
	for frame in range(replay_start + 1, final_frame + 1):
		assert(battle.advance(frame, _players(frame, attack_start)).is_empty())
	battle.end_replay()
	assert(State.first_difference(expected, battle.save_state()).is_empty())
	# nextfight restores HP/standing through the shared source round controller.
	game.naruto.health = 0
	game.naruto.sw = true
	game.ko_timeline.controller.nextfight()
	assert(game.naruto.health == game.session.maxhp and not game.naruto.sw)
	assert(game.naruto.current_source_frame() == 1)
	Fixture.dispose(game, battle)
	await process_frame
	print("ITACHI_COUNTER_ROLLBACK_SMOKE_OK intro=natural checkpoint=449 round_reset=true")
	quit()
