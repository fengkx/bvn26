extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _check_fighters(game: Node) -> void:
	for fighter: FighterRuntime in [game.naruto, game.ichigo]:
		fighter.energy = 300
		fighter.goto_ai_label("站立", false)
		var frame := fighter.current_source_frame()
		assert(not fighter.start_command("万解"))
		fighter.start_action("万解")
		fighter.goto_ai_label("万解", true)
		assert(fighter.action == "站立" and fighter.current_source_frame() == frame)
		assert(fighter.energy == 300)
		assert(fighter.start_command("砍1"))

func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	_check_fighters(game)
	game._replace_selected_actors(["日番谷", "鸣人"], ["我爱罗", "魂"])
	_check_fighters(game)
	game.queue_free()
	await process_frame
	print("TRANSFORMATION_GATE_SMOKE_OK")
	quit()
