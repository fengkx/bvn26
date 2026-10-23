extends SceneTree
const Fixture = preload("res://tests/rollback_fixture.gd")
const Inputs = preload("res://rollback_test_session.gd")
const State = preload("res://simulation_state.gd")


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fixture := Fixture.create(self, ["带土", "一护"], ["鼬", "魂"])
	var game: Node = fixture.game
	var battle: RefCounted = fixture.battle
	assert(game.recorded_form_timers and game.source_root_intervals.recorded)
	game.battle_intro.active = false
	game.battle_intro.polling = false
	game.super_runtime.zhanting = false
	game.naruto.root_zhanting = false
	game.ichigo.root_zhanting = false
	game.naruto.health = 500
	game.naruto.ai_source_state.values.wudi = true
	var callback := preload("res://source_slot_health_callback.gd").new()
	callback.target = weakref(game.naruto)
	callback.root_values = game.source_form_root_values
	var id: int = game.source_root_intervals.assign_interval("feiint", callback.deliver, 1000)
	assert(not battle.set_frame_events(1, 1000, false, [{"kind": "root_interval", "phase": "after_actor_advance", "id": 0}]).is_empty())
	assert(battle.set_frame_events(1, 1000, false, [{"kind": "root_interval", "phase": "after_actor_advance", "id": id}]).is_empty())
	var players := {"p1": {}, "p2": {}}
	for slot in players:
		for button in Inputs.BUTTONS: players[slot][button] = false
	var before: Dictionary = battle.save_state()
	assert(not before.has("error"), str(before))
	assert(battle.advance(1, players).is_empty())
	assert(game.naruto.health == 490, str(game.naruto.health) + " paused=" + str(game.naruto.root_zhanting))
	assert(game.source_root_intervals.pending_count() == 1)
	var after: Dictionary = battle.save_state()
	assert(not after.has("error"), str(after))
	assert(battle.load_state(before).is_empty())
	assert(game.naruto.health == 500)
	assert(battle.advance(1, players).is_empty())
	assert(game.naruto.health == 490, str(game.naruto.health) + " paused=" + str(game.naruto.root_zhanting))
	assert(State.first_difference(after, battle.save_state()).is_empty())
	print("FORM_ROOT_INTERVAL_REPLAY_OK recorded_envelope validation repeating_callback full_restore_and_redelivery")
	Fixture.dispose(game, battle)
	await process_frame
	quit()
