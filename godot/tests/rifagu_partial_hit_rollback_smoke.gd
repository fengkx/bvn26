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
	players.p1.down = attack_start > 0 and frame >= attack_start and frame <= attack_start + 3
	players.p1.special = players.p1.down
	return players


func _run() -> void:
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FighterSelection.CATALOG_PATH))
	var selected_name := ""
	for display_name in catalog.fighters:
		if catalog.fighters[display_name] == "rifagu-2":
			selected_name = display_name
	assert(not selected_name.is_empty())
	var fixture := Fixture.create(self, [selected_name, "鸣人"], ["我爱罗", "魂"], "现世")
	var game: Node = fixture.game
	var battle: RefCounted = fixture.battle
	game.naruto.energy = 300
	# Use the same starting separation as the native Flash ultimate fixture.
	game.naruto.position.x = 300
	game.ichigo.position.x = 350
	var checkpoint := {}
	var replay_start := 0
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
		if attack_start > 0 and game.ichigo.ai_source_state.read_field("htx") == null and checkpoint.is_empty():
			assert(is_nan(game.ichigo._hurt_horizontal_step))
			checkpoint = battle.save_state()
			replay_start = frame
		if frame % 60 == 0:
			await process_frame
		if attack_start > 0 and frame == attack_start + 380:
			final_frame = frame
			break
	assert(not checkpoint.is_empty() and final_frame > 0 and not game.battle_intro.active)
	assert(game.naruto.energy == 0)
	assert(game.ichigo.health < game.session.maxhp, "Source ultimate must reach the opponent")
	var expected: Dictionary = battle.save_state()
	battle.begin_replay()
	assert(battle.load_state(checkpoint).is_empty())
	for frame in range(replay_start + 1, final_frame + 1):
		assert(battle.advance(frame, _players(frame, attack_start)).is_empty())
	battle.end_replay()
	assert(State.first_difference(expected, battle.save_state()).is_empty())
	Fixture.dispose(game, battle)
	await process_frame
	print("RIFAGU_PARTIAL_HIT_ROLLBACK_OK undefined_packet=true checkpoint_replay=true")
	quit()
