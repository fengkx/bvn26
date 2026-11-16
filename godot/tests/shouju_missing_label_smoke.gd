extends SceneTree

const Fixture = preload("res://tests/rollback_fixture.gd")
const Inputs = preload("res://rollback_test_session.gd")


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fixture := Fixture.create(self, ["手鞠", "一护"], ["我爱罗", "魂"])
	var game: Node = fixture.game
	var battle: RefCounted = fixture.battle
	assert(game.naruto.action_range("万解").is_empty())
	# Source jump/normal predicates reject J+K; wankai requests an absent label.
	# Verify the source no-op without the deferred-form gate.
	game.naruto.disabled_actions.clear()
	game.naruto.energy = 300
	var start := -1
	var input_ticks := 0
	for frame in range(1, 600):
		if not game.battle_intro.active and start < 0:
			start = frame
		var players := {"p1": {}, "p2": {}}
		for slot in players:
			for button in Inputs.BUTTONS:
				players[slot][button] = false
		players.p1.attack = start > 0 and frame < start + 4
		players.p1.jump = players.p1.attack
		var callbacks := []
		if game.battle_intro.polling and frame % 15 == 0:
			callbacks.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": frame, "time_ms": frame * 33})
		assert(battle.set_frame_events(frame, frame * 33, false, callbacks).is_empty())
		assert(battle.advance(frame, players).is_empty())
		if start > 0:
			assert(game.naruto.action == "站立")
		if players.p1.attack:
			input_ticks += 1
		assert(game.naruto.source_parent_frame == 1)
		if start > 0 and frame >= start + 90:
			break
		if frame % 60 == 0:
			await process_frame
	assert(start > 0 and input_ticks == 4)
	assert(game.naruto.disabled_actions.is_empty())
	assert(game.naruto.energy == 300)
	Fixture.dispose(game, battle)
	await process_frame
	print("SHOUJU_MISSING_LABEL_OK disabled_actions_empty=true source_attack_jump=true parent_frame=1 energy=300")
	quit()
