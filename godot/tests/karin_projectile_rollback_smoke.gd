extends SceneTree

const Fixture = preload("res://tests/rollback_fixture.gd")
const Inputs = preload("res://rollback_test_session.gd")
const State = preload("res://simulation_state.gd")

var case_inputs: Array = []


func _initialize() -> void:
	_run.call_deferred()


func _inputs(tick: int) -> Dictionary:
	var players := {"p1": {}, "p2": {}}
	for slot in players:
		for button in Inputs.BUTTONS:
			players[slot][button] = false
	for input: Dictionary in case_inputs:
		if tick >= int(input.start) and tick <= int(input.end):
			for key: String in input.keys:
				players[input.slot][key] = true
	return players


func _run() -> void:
	var source_case: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(
		"res://../evidence/characters/karin/cases/repeat-ranged.json"))
	case_inputs = source_case.inputs
	var fixture := Fixture.create(self, ["香磷", "一护"], ["我爱罗", "魂"], "现世")
	var game: Node = fixture.game
	var battle: RefCounted = fixture.battle
	var start := -1
	var checkpoint := {}
	var checkpoint_frame := 0
	var final_frame := 0
	var cast_facings: Array = []
	for frame in range(1, 1101):
		if not game.battle_intro.active and start < 0:
			start = frame
			game.naruto.energy = 300
			game.naruto.position.x = 300
			game.ichigo.position.x = 350
		var callbacks := []
		if game.battle_intro.polling and frame % 15 == 0:
			callbacks.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": frame, "time_ms": frame * 33})
		assert(battle.set_frame_events(frame, frame * 33, false, callbacks).is_empty())
		assert(battle.advance(frame, _inputs(frame - start + 1 if start > 0 else -1)).is_empty())
		if game.naruto.current_source_frame() == 444:
			cast_facings.append(game.naruto.scale.x)
		if checkpoint.is_empty() and start > 0:
			for model: Dictionary in game.naruto._combat.projectiles:
				if int(model.start_frame) != 448:
					continue
				var variables: Dictionary = game.naruto.instance_source_variables(model.instance_name)
				if variables.is_empty():
					continue
				assert(variables.atm_name == "zh1atm")
				assert(variables.movspeed == (0 if variables.played == 1 else 20))
				checkpoint = battle.save_state()
				checkpoint_frame = frame
		if start > 0 and frame == start + 360:
			final_frame = frame
			break
		if frame % 60 == 0:
			await process_frame
	assert(not checkpoint.is_empty() and final_frame > 0)
	assert(game.ichigo.health < game.session.maxhp)
	assert(cast_facings == [1.0, -1.0, 1.0], "Repeated projectiles must exercise both facings")
	var expected: Dictionary = battle.save_state()
	battle.begin_replay()
	assert(battle.load_state(checkpoint).is_empty())
	for frame in range(checkpoint_frame + 1, final_frame + 1):
		assert(battle.advance(frame, _inputs(frame - start + 1)).is_empty())
	battle.end_replay()
	assert(State.first_difference(expected, battle.save_state()).is_empty())
	Fixture.dispose(game, battle)
	await process_frame
	print("KARIN_PROJECTILE_ROLLBACK_SMOKE_OK casts=3 side_switches=2")
	quit()
