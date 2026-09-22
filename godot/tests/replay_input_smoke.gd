extends "res://tests/intro_continuous_reference.gd"


func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game._enter_current_fight(2)
	bind_recorded_input(game)
	var fields := ["right", "attack", "down", "ranged", "jump", "special", "summon"]
	for field: String in fields:
		apply_recorded_input(game, field + "=true", 100)
		game._advance_fight()
		var held: Dictionary = game._input_for(game.naruto)
		for candidate: String in fields:
			assert(held[candidate] == (candidate == field))
		var count := input_transitions.size()
		apply_recorded_input(game, field + "=true", 101)
		assert(input_transitions.size() == count)
		assert(game._input_for(game.ichigo).is_empty())
	apply_recorded_input(game, "", 102)
	game._advance_fight()
	for value in game._input_for(game.naruto).values():
		assert(not value)
	game._goto_menu()
	game.queue_free()
	await process_frame
	print("REPLAY_INPUT_SMOKE_OK")
	quit()
