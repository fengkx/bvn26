extends SceneTree

var failure := false


func _initialize() -> void:
	_run.call_deferred()


func check(condition: bool, message: String) -> void:
	if not condition:
		push_error(message)
		failure = true


func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game._enter_current_fight(3)
	var intro: BattleIntro = game.battle_intro
	check(intro.active and game.naruto.root_zhanting and game.ichigo.root_zhanting, "Opening must lock both players")
	# The original polls at 500 ms; neither player starts on placement.
	for i in 14:
		game._advance_fight()
	check(intro.step == 0, "kaichang fired before 500 ms")
	game._advance_fight()
	check(intro.step == 1, "First poll must open qjxg")
	for i in 15:
		game._advance_fight()
	check(intro.step == 2 and game.naruto.action == "开场", "P1 must enter its own opening label")
	check(game.ichigo.action == "站立", "P2 must wait for P1 completion")
	var p1_x: float = game.naruto.position.x
	game.naruto.enter_frame({"right": true, "attack": true, "summon": true})
	check(game.naruto.position.x == p1_x and game.naruto.action == "开场", "Opening accepted combat input")
	var saw_p2 := false
	for i in 200:
		game._advance_fight()
		if intro.step == 3:
			saw_p2 = true
			check(intro.states[0] == 2, "P2 started before source kcplayed=2")
		if intro.step == 4:
			break
	check(saw_p2 and intro.states == [2, 2], "Both character opening scripts must complete")
	check(intro.focus == "all", "ROUND must focus both players")
	for i in 132:
		if intro.clips["ready"].current_source_frame() >= 126:
			break
		game._advance_fight()
	check(intro.active and game.naruto.root_zhanting, "Combat unlocked before ready frame 127")
	game._advance_fight()
	check(not intro.active and not game.naruto.root_zhanting, "ready frame 127 must startFight")
	for i in 8:
		game._advance_fight()
	check(intro.clips["ready"].current_source_frame() == 1 and not intro.playing["ready"], "ready must wrap to stopped frame 1")
	# Exercise the separate source skipintro path during either player's intro.
	for target in [2, 3]:
		game._enter_current_fight(3)
		for i in 180:
			game._advance_fight()
			if intro.step == target:
				break
		intro.tick(1.0 / 30.0, true)
		check(intro.active and intro.step == 4, "Skip must not unlock immediately")
		check(intro.clips["qjxg"].current_source_frame() == 33, "Skip must use source skipintro label")
		for i in 3:
			game._advance_fight()
		check(game.naruto.action == "站立" and game.ichigo.action == "站立", "qjxg 36 must reset both fighters")
		check(intro.active, "qjxg 36 must stay locked")
		for i in 4:
			game._advance_fight()
		check(not intro.active, "qjxg 40 must unlock")
	game._enter_current_fight(4)
	check(intro.active and intro.states == [0, 0], "Re-entry must reset intro state in training")
	game._goto_menu()
	check(not intro.active and not intro.clips["ready"].visible, "Returning to menu leaked opening")
	for node in game.find_children("*", "AudioStreamPlayer", true, false):
		node.stop()
	await create_timer(0.1).timeout
	game.queue_free()
	await process_frame
	await create_timer(0.1).timeout
	print("INTRO_SMOKE_OK" if not failure else "INTRO_SMOKE_FAILED")
	quit(1 if failure else 0)
