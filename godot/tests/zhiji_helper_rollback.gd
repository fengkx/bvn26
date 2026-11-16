extends SceneTree

const Fixture = preload("res://tests/rollback_fixture.gd")
const Inputs = preload("res://rollback_test_session.gd")
const State = preload("res://simulation_state.gd")


func _initialize() -> void:
	_run.call_deferred()


func _players(tick: int) -> Dictionary:
	var players := {"p1": {}, "p2": {}}
	for slot in players:
		for button in Inputs.BUTTONS:
			players[slot][button] = false
	for start in [10, 130, 250]:
		if tick >= start and tick < start + 3:
			players.p1.summon = true
	players.p2.left = tick >= 110 and tick < 125
	players.p2.right = tick >= 230 and tick < 245
	return players


func _run() -> void:
	var fixture := Fixture.create(self, ["一护", "鸣人"], ["织姬", "魂"], "现世")
	var game: Node = fixture.game
	var battle: RefCounted = fixture.battle
	var attack_start := -1
	var checkpoint := {}
	var checkpoint_frame := -1
	var final_frame := -1
	var original_helper: HelperRuntime = game.naruto_helper
	var paused := false
	for frame in range(1, 1001):
		if not game.battle_intro.active and attack_start < 0:
			attack_start = frame
			game.naruto.health = 600
			game.naruto.energy = 300
			game.ichigo.energy = 300
			game.naruto.position.x = 300
			game.ichigo.position.x = 450
		var callbacks := []
		if game.battle_intro.polling and frame % 15 == 0:
			callbacks.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": frame, "time_ms": frame * 33})
		assert(battle.set_frame_events(frame, frame * 33, false, callbacks).is_empty())
		assert(battle.advance(frame, _players(frame - attack_start) if attack_start >= 0 else _players(-1)).is_empty())
		if attack_start >= 0:
			paused = paused or game.super_runtime.zhanting
			if game.naruto.health == 620 and checkpoint.is_empty():
				checkpoint = battle.save_state()
				checkpoint_frame = frame
			if frame == attack_start + 390:
				final_frame = frame
				break
		if frame % 60 == 0:
			await process_frame
	assert(final_frame > 0 and checkpoint_frame > 0 and paused)
	assert(game.naruto_helper == original_helper, "All casts must reuse the helper instance")
	assert(game.naruto.health == 1020, "Original three-cast capture adds 21 separate 20-HP writes")
	assert(game.ichigo.health == 1000)
	assert(not original_helper.attacking and not original_helper.visible)
	assert(original_helper.current_source_frame() == 1)
	var expected: Dictionary = battle.save_state()
	battle.begin_replay()
	assert(battle.load_state(checkpoint).is_empty())
	for frame in range(checkpoint_frame + 1, final_frame + 1):
		assert(battle.advance(frame, _players(frame - attack_start)).is_empty())
	battle.end_replay()
	var difference: String = State.first_difference(expected, battle.save_state())
	assert(difference.is_empty(), difference)
	# Source nextfight calls chushi to reset HP; it does not replace helper roots.
	# This is a direct callback invariant check, not a full original KO replay.
	var retained_energy: float = game.naruto.energy
	game.ko_timeline.controller.nextfight()
	assert(game.naruto.health == game.session.maxhp and game.ichigo.health == game.session.maxhp)
	assert(game.naruto.energy == retained_energy)
	assert(game.naruto_helper == original_helper and not original_helper.attacking)
	for tick in 700:
		game._advance_fight()
		if not game.battle_intro.active:
			break
	assert(not game.battle_intro.active)
	# Explicit diagnostic resource precondition, as in the source replay fixtures.
	game.naruto.energy = 100
	game.naruto.enter_frame({"summon": true})
	for tick in 180:
		game._advance_fight()
	assert(game.naruto_helper == original_helper)
	assert(game.naruto.health == game.session.maxhp + 140)
	assert(game.naruto.energy == 0 and not original_helper.attacking)
	battle.close()
	game._stop_combat_drivers()
	game.queue_free()
	await process_frame
	battle = null
	fixture.clear()
	assert(await preload("res://tests/audio_shutdown.gd").drain(self))
	print("ZHIJI_HELPER_ROLLBACK_OK repeat=3 health=1020 pause=true same_instance=true checkpoint_replay=true round_callback=true post_round_heal=1140")
	quit()
