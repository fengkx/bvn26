extends SceneTree

var game

func _initialize() -> void:
	_run.call_deferred()

func _shadows() -> Array:
	return game.game_world.get_children().filter(func(node): return node.has_meta("source_shadow"))

func _run() -> void:
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game._enter_current_fight(3)
	for tick in 700:
		game._advance_fight()
		if not game.battle_intro.active:
			break
	for pair: Array in [["鸣人", "一护"], ["日番谷", "鸣人"]]:
		game._replace_selected_actors(pair, ["我爱罗", "魂"])
		game._enter_current_fight(2)
		for tick in 700:
			game._advance_fight()
			if not game.battle_intro.active:
				break
		for actor: FighterRuntime in [game.naruto, game.ichigo]:
			for direction in [1, -1]:
				actor.position = Vector2(300, -25)
				actor.set_facing(direction)
				actor.goto_ai_label("走", false)
				var previous_size := _shadows().size()
				game._fighter_visual_service(actor, "showdow", [{"R":20, "G":-100, "B":255}])
				assert(_shadows().size() == previous_size + 1, "First call creates a snapshot")
				var shadow: ShadowSnapshot = _shadows().back()
				assert(shadow.z_index < actor.z_index and shadow.scale.x == direction)
				var frozen_position := shadow.position
				var frozen_size := shadow.bitmap_size
				var frozen_frame := shadow.captured_frame
				assert(shadow.capture_viewport.get_child(0).get_child_count() > 0)
				actor.position += Vector2(70, -80)
				actor.goto_ai_label("站立", true)
				game._fighter_visual_service(actor, "showdow", [{"R":20, "G":-100, "B":255}])
				assert(_shadows().size() == previous_size + 1, "Action entry must not reset the wrapper counter")
				actor.root_zhanting = true
				for alpha in [89.84375,79.6875,69.53125,59.375,49.21875,39.0625,28.90625,18.75,8.59375,-1.171875]:
					shadow.fade()
					assert(shadow.source_alpha == alpha)
					assert(shadow.position == frozen_position and shadow.bitmap_size == frozen_size and shadow.captured_frame == frozen_frame)
				assert(_shadows().size() == previous_size)
				actor.root_zhanting = false
			print("SHADOW_ACTOR_OK ", actor.fighter_name)
		# Leaving with a live snapshot must unregister it before registry teardown.
		game._fighter_visual_service(game.naruto, "showdow", [{}])
		game._goto_menu()
		assert(_shadows().is_empty())
		await process_frame
	game.queue_free()
	await process_frame
	print("SHADOW_SMOKE_OK")
	quit()
