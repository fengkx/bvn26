extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game._replace_selected_actors(["日番谷", "一护"], ["我爱罗", "魂"])
	game._load_selected_stage("现世")
	game._enter_current_fight(3)
	for tick in 700:
		game._advance_fight()
		if not game.battle_intro.active:
			break
	# Keep the same actor instances, as in repeated casts in a live match.
	for positions: Array in [[300.0, 700.0], [700.0, 100.0], [200.0, 550.0]]:
		game.naruto.goto_ai_label("站立", true)
		game.ichigo.goto_ai_label("站立", true)
		game._advance_fight()
		game.naruto.position = Vector2(positions[0], -25)
		game.ichigo.position = Vector2(positions[1], -25)
		game.naruto.set_facing(1 if positions[0] < positions[1] else -1)
		game.naruto.energy = 300
		game.naruto.goto_ai_label("超必杀", true)
		for tick in 100:
			game._advance_fight()
			if game.naruto.current_source_frame() == 670:
				break
		assert(game.naruto.current_source_frame() == 670)
		var expected := Vector2((game.ichigo.position.x - game.naruto.position.x) * game.naruto.facing,
			game.ichigo.position.y - game.naruto.position.y)
		var actual: Vector2 = game.naruto.named_instance_origin("cbs1atm") + game.naruto.instance_local_offset("cbs1atm")
		print("REPEATED_ICE_POSITION ", positions, " expected=", expected, " actual=", actual)
		if not actual.is_equal_approx(expected):
			push_error("A new cast must execute frame 670's opponent-relative assignment")
			quit(1)
			return
		# Frame 671 retains the placement; it must not continuously chase P2.
		game.ichigo.position.x += 20
		game._advance_fight()
		actual = game.naruto.named_instance_origin("cbs1atm") + game.naruto.instance_local_offset("cbs1atm")
		assert(actual.is_equal_approx(expected))
	game._goto_menu()
	print("REPEATED_CLIP_PLACEMENT_SMOKE_OK")
	quit()
