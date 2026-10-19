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
	players.p1.up = attack_start > 0 and frame >= attack_start and frame <= attack_start + 3
	players.p1.special = players.p1.up
	players.p2.down = attack_start > 0 and frame >= attack_start
	return players


func _run() -> void:
	var fixture := Fixture.create(self, ["带土", "一护"], ["我爱罗", "魂"], "现世")
	var game: Node = fixture.game
	var battle: RefCounted = fixture.battle
	game.naruto.energy = 300
	# Match the controlled original-player upper-super fixture after natural opening.
	game.naruto.position.x = 300
	game.ichigo.position.x = 350
	var initial: Dictionary = battle.save_state()
	var paused := false
	var checkpoint := {}
	var replay_start := 0
	var hidden_checkpoint := {}
	var hidden_frame := 0
	var attack_start := -1
	var final_frame := 0
	for frame in range(1, 901):
		if not game.battle_intro.active and attack_start < 0:
			attack_start = frame
		var callbacks := []
		if game.battle_intro.polling and frame % 15 == 0:
			callbacks.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": frame, "time_ms": frame * 33})
		assert(battle.set_frame_events(frame, frame * 33, false, callbacks).is_empty())
		assert(battle.advance(frame, _players(frame, attack_start)).is_empty())
		if attack_start > 0 and game.naruto.root_zhanting and checkpoint.is_empty():
			assert(game.naruto.action == "上必杀")
			checkpoint = battle.save_state()
			replay_start = frame
			paused = true
		if not game.ichigo.visible and hidden_checkpoint.is_empty():
			hidden_checkpoint = battle.save_state()
			hidden_frame = frame
		if frame % 60 == 0:
			await process_frame
		if attack_start > 0 and frame == attack_start + 300:
			final_frame = frame
			break
	assert(paused and final_frame > 0 and not game.battle_intro.active)
	assert(game.naruto.action == "站立" and game.naruto.energy == 200)
	assert(game.ichigo.health < game.session.maxhp, "Source upper super must reach the guarding opponent")
	var expected: Dictionary = battle.save_state()
	battle.begin_replay()
	assert(battle.load_state(checkpoint).is_empty())
	for frame in range(replay_start + 1, final_frame + 1):
		assert(battle.advance(frame, _players(frame, attack_start)).is_empty())
	battle.end_replay()
	assert(State.first_difference(expected, battle.save_state()).is_empty())
	assert(not hidden_checkpoint.is_empty() and game.ichigo.visible)
	battle.begin_replay()
	assert(battle.load_state(hidden_checkpoint).is_empty())
	assert(not game.ichigo.visible)
	for frame in range(hidden_frame + 1, final_frame + 1):
		assert(battle.advance(frame, _players(frame, attack_start)).is_empty())
	battle.end_replay()
	assert(State.first_difference(expected, battle.save_state()).is_empty())
	# Deliver three guard inputs late through the production rollback session.
	assert(battle.load_state(initial).is_empty())
	var session := Inputs.new()
	assert(session.configure(battle, "daitu-late-guard", 8, 12).is_empty())
	for frame in range(1, final_frame + 1):
		assert(session.receive(session.epoch, "p1", frame, _players(frame, attack_start).p1).is_empty())
		if frame == attack_start + 3:
			for delayed in range(attack_start, frame):
				assert(session.receive(session.epoch, "p2", delayed, _players(delayed, attack_start).p2).is_empty())
		if frame < attack_start or frame >= attack_start + 3:
			assert(session.receive(session.epoch, "p2", frame, _players(frame, attack_start).p2).is_empty())
		assert(session.step().is_empty())
		if frame % 60 == 0:
			await process_frame
	assert(session.rollback_count > 0)
	assert(State.first_difference(expected, battle.save_state()).is_empty())
	# nextfight restores HP/standing through the shared source round controller.
	game.naruto.health = 0
	game.naruto.sw = true
	game.ko_timeline.controller.nextfight()
	assert(game.naruto.health == game.session.maxhp and not game.naruto.sw)
	assert(game.naruto.current_source_frame() == 1)
	Fixture.dispose(game, battle)
	await process_frame
	print("DAITU_ROLLBACK_SMOKE_OK intro=natural super=upper guard=true round_reset=true late_input=true")
	quit()
