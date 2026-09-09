extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game._enter_current_fight(2)
	game.ichigo.ai_random_clock.cancel()
	for fighter: FighterRuntime in [game.naruto, game.ichigo]:
		fighter.energy = 187.5
		fighter.hits = 2
		fighter.root_zhanting = true
		fighter.health = 0
		fighter.sw = true
		fighter.goto_ai_label("被打", true)
		fighter._ai_pending_frames.clear()
	game.ko_timeline.controller.nextfight()
	for fighter: FighterRuntime in [game.naruto, game.ichigo]:
		if fighter.energy != 187.5 or fighter.hits != 2 or not fighter.root_zhanting or fighter.health != game.session.maxhp or fighter.sw:
			push_error("nextfight must retain source energy, hits and pause until BODY scripts run")
			quit(1)
			return
		if fighter._ai_pending_frames.size() != 1 or fighter.current_source_frame() != 1:
			push_error("Repeated goto of standing must queue its frame script once")
			quit(1)
			return
	game._goto_menu()
	game.queue_free()
	await process_frame
	print("ROUND_RESET_SMOKE_OK")
	quit()
