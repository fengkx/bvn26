extends SceneTree
const Fixture = preload("res://tests/rollback_fixture.gd")
const Inputs = preload("res://rollback_test_session.gd")
var passed := 0


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	for profile: Dictionary in [{"id": "minren", "name": "鸣人"}, {"id": "daitu", "name": "带土"}, {"id": "sasuke", "name": "佐助"}, {"id": "rukia", "name": "露其雅"}, {"id": "byakuya", "name": "白哉"}, {"id": "rifagu", "name": "日番谷"}]:
		await _case(profile)
	assert(passed == 6)
	print("FORM_INPUT_ACTIVATION_OK 6/6 accepted graphs; source_attack_jump energy300 natural_intro real_form_action_and_replacement")
	quit()


func _case(profile: Dictionary) -> void:
	var fixture := Fixture.create(self, [profile.name, "一护"], ["鼬", "魂"])
	var game: Node = fixture.game
	var battle: RefCounted = fixture.battle
	assert("万解" not in game.naruto.disabled_actions)
	var opponent_has_graph := FileAccess.file_exists(game.ichigo.fighter_directory.path_join("form_profiles.json"))
	assert(("万解" in game.ichigo.disabled_actions) == not opponent_has_graph)
	assert(game.naruto.ai_source_state.read_field("pn") == 2, "Initial source body must bind the opponent slot")
	game.naruto.energy = 300
	var attack_start := -1
	var entered := false
	var replaced := false
	for frame in range(1, 901):
		if not game.battle_intro.active and attack_start < 0:
			attack_start = frame
		var players := {"p1": {}, "p2": {}}
		for slot in players:
			for button in Inputs.BUTTONS: players[slot][button] = false
		players.p1.attack = attack_start > 0 and frame < attack_start + 4
		players.p1.jump = players.p1.attack
		var callbacks := []
		if game.battle_intro.polling and frame % 15 == 0:
			callbacks.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": frame, "time_ms": frame * 33})
		assert(battle.set_frame_events(frame, frame * 33, false, callbacks).is_empty())
		assert(battle.advance(frame, players).is_empty())
		entered = entered or game.naruto.action == "万解"
		if game.naruto.source_parent_frame == 2 and game.naruto.source_body_available:
			replaced = true
			break
	assert(entered and replaced, "Source attack+jump must reach the accepted form graph")
	assert(game.naruto.fighter_directory == "res://generated/forms/" + str(profile.id) + "-2")
	assert(game.match_input.error.is_empty(), game.match_input.error)
	var transfer: Dictionary = game.player_body_driver._driver.source_form_context.transfer
	assert(transfer.get("hp") != null and transfer.get("ql") != null)
	assert(game.naruto.source_health_defined and game.naruto.health == transfer.hp and game.naruto.energy == transfer.ql)
	passed += 1
	print("FORM_INPUT_CASE_OK ", profile.id)
	for audio: AudioStreamPlayer in game.find_children("*", "AudioStreamPlayer", true, false):
		audio.stop()
		audio.stream = null
	Fixture.dispose(game, battle)
	await create_timer(0.1).timeout
