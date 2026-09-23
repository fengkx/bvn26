extends RefCounted

const Battle = preload("res://rollback_battle.gd")

static func create(tree: SceneTree, fighters: Array = [], helpers: Array = [], stage: String = "") -> Dictionary:
	var game = load("res://main.tscn").instantiate()
	tree.root.add_child(game)
	game.set_physics_process(false)
	game.set_process(false)
	game.ko_recorded_timers = true
	game.recorded_training_timers = true
	game.source_random.use_seed(727)
	game.source_clock.use_explicit_time(0)
	if not fighters.is_empty(): game._replace_selected_actors(fighters, helpers)
	if not stage.is_empty(): game._load_selected_stage(stage)
	game._enter_current_fight(3)
	game.battle_intro.recorded_polling = true
	for timer in game.title_menu.find_children("*", "Timer", true, false): timer.stop()
	var battle := Battle.new()
	var problem := battle.configure(game)
	assert(problem.is_empty(), problem)
	return {"game": game, "battle": battle}

static func dispose(game: Node, battle: RefCounted) -> void:
	battle.close()
	game._goto_menu()
	game.free()
