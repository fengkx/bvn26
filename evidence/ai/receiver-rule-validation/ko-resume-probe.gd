# Expected to fail until KO scripts share the instance scheduler.
extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game._enter_current_fight(2)
	game.ichigo.ai_random_clock.cancel()
	for tick in 600:
		game._advance_fight()
		if not game.battle_intro.active:
			break
	assert(not game.battle_intro.active)
	for fighter: FighterRuntime in [game.naruto, game.ichigo]:
		fighter.goto_ai_label("站立", true)
		fighter.run_frame_actions()
	game._ko_service("call", ["KOstart"])
	game.ko_timeline._goto(game.ko_timeline.root_clip, 29, true)
	var before: Array = [game.naruto.current_source_frame(), game.ichigo.current_source_frame()]
	game._advance_fight()
	assert(game.ko_timeline.root_clip.frame == 30)
	assert(not game.naruto.root_zhanting and not game.ichigo.root_zhanting)
	var after: Array = [game.naruto.current_source_frame(), game.ichigo.current_source_frame()]
	# Source r15 49224–49228: KO frame 30 resumes the actors after their
	# paused callbacks, so the same root snapshot retains their playheads.
	if after != before:
		push_error("KO frame 30 must not advance resumed actors in the same display tick")
		quit(1)
		return
	game._goto_menu()
	game.queue_free()
	await process_frame
	print("VS_COM_KO_RESUME_SMOKE_OK")
	quit()
