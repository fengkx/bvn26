extends Node

func _ready() -> void:
	run.call_deferred()

func run() -> void:
	for name_value in ["手鞠", "夜一", "天天", "志志雄", "自来也", "蒂雅", "葛力姆乔", "四代", "史塔克", "纲手", "八千流", "牛头白一护", "雏田", "碎蜂", "水月", "涅音梦", "斑"]:
		var game = load("res://main.tscn").instantiate()
		add_child(game)
		game.set_physics_process(false)
		await get_tree().process_frame
		game._goto_character_selection(3)
		var menu = game.character_selection
		menu.fighters = ["一护", "鸣人"]
		menu._enter_phase(1)
		for card in menu.cards:
			if card.id == name_value:
				menu._select_grid(Vector2i(card.grid[0], card.grid[1]), 0)
		if menu.helpers[0] != name_value:
			print("LIVE_FAIL select ", name_value)
			return
		game.ko_recorded_timers = true
		game.recorded_training_timers = true
		game._on_characters_confirmed(menu.fighters.duplicate(), [menu.helpers[0], "魂"])
		game._on_map_confirmed("现世")
		for tick in 700:
			game._advance_fight()
			if not game.battle_intro.active:
				break
			if tick % 30 == 0:
				await get_tree().process_frame
		if game.battle_intro.active or game.naruto_helper.helper_id != name_value:
			print("LIVE_FAIL intro ", name_value)
			return
		game.naruto.position.x = 300
		game.ichigo.position.x = 450
		game.naruto.energy = 300
		var helper = game.naruto_helper
		var active_ticks := 0
		var visible_frames := 0
		print("LIVE_KEY ", name_value)
		for tick in 1300:
			await get_tree().process_frame
			game._advance_fight()
			if helper.attacking:
				active_ticks += 1
				if helper.visible and helper.visual_child_count() > 0:
					visible_frames += 1
				if active_ticks == 30:
					print("LIVE_SCREEN ", name_value)
			elif active_ticks > 0:
				break
		print("LIVE_RESULT ", JSON.stringify({"name":name_value,"active":active_ticks,"drawn":visible_frames,"parked":not helper.attacking and helper.current_source_frame()==1,"opponent_hp":game.ichigo.health,"helper":helper.helper_id}))
		game._stop_combat_drivers()
		game.queue_free()
		await get_tree().process_frame
		await get_tree().process_frame
	print("LIVE_DONE")
