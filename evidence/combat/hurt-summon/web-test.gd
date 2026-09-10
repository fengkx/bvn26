extends Node

func _ready() -> void:
	_run.call_deferred()

func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	get_tree().root.add_child(game)
	game.set_physics_process(false)
	for pair: Array in [["一护", "鸣人"], ["鸣人", "日番谷"]]:
		game._replace_selected_actors(pair, ["我爱罗", "我爱罗"])
		game._load_selected_stage("现世")
		game._enter_current_fight(2)
		for tick in 700:
			game._advance_fight()
			if not game.battle_intro.active:
				break
		for actor: FighterRuntime in [game.naruto, game.ichigo]:
			actor.goto_ai_label("站立", true)
			actor.run_frame_actions()
		var driver: AiCpuDriver = game.opponent_driver
		var cpu: FighterRuntime = game.ichigo
		cpu.energy = 300
		cpu.source_x = 700
		cpu.source_y = -125
		cpu.set_facing(-1)
		game.naruto.source_x = 100
		cpu.ai_source_state.values.merge({"goran": 0, "hstm": 0, "time": 0,
			"htx": 0, "yup": 0, "tdtime": 50, "touch": false}, true)
		driver.timeouts.recorded = true
		var registered: Array = []
		driver.timeouts.registered.connect(func(id: int, delay: int) -> void: registered.append([id, delay]))
		driver.body.beidax(false)
		var naruto_branch: bool = pair[1] == "鸣人"
		var expected_xg := "XG_tishen" if naruto_branch else "XG_bsq"
		print("ESCAPE_FACTION ", pair, " flag=", driver.body_context.is_naruto,
			" effect=", game.super_runtime.last_xg, " timeout=", registered,
			" x=", cpu.source_x, " energy=", cpu.energy)
		if game.super_runtime.last_xg != expected_xg:
			push_error("Escape branch must follow source fighter catalog, not P1/P2 or CPU/player role")
			JavaScriptBridge.eval("window.hurtSummonResult = 'failed'")
			return
		assert(cpu.energy == 200 and registered.size() == 1)
		assert(registered[0][1] == (800 if naruto_branch else 600))
		assert(cpu.source_x == (550 if naruto_branch else 700))
		if naruto_branch:
			var clips := {}
			for child in game.game_world.get_children():
				if child is HitEffectRuntime and child._directory.get_file() in ["XG_tishen", "XG_tishen2"]:
					clips[child._directory.get_file()] = child
			assert(clips.size() == 2)
			assert(clips.XG_tishen.position == Vector2(700, -150))
			assert(clips.XG_tishen2.position == Vector2(550, -125))
			for clip: HitEffectRuntime in clips.values():
				assert(clip.scale.x == -1 and clip._preview.get_child_count() > 0)
		assert(game.player_body_driver.context.is_naruto == (pair[0] == "鸣人"))
		assert(driver.timeouts.fire_recorded(registered[0][0]))
		assert(game.cpu_services.stage_effects.size() == (0 if naruto_branch else 1))
		assert(cpu.helper_spawn.is_empty())
		if not naruto_branch:
			for tick in 50:
				cpu.run_frame_actions()
				assert(cpu.helper_spawn.is_empty() and cpu.energy == 200 and cpu.bs == 0)
				if cpu.action == "站立":
					break
				cpu.advance_ai_timeline()
			assert(cpu.action == "站立")
			print("ESCAPE_SUMMON_GUARD_OK ", pair[1])
		game._goto_menu()
		await get_tree().process_frame
	game._replace_selected_actors(["一护", "鸣人"], ["我爱罗", "我爱罗"])
	game._load_selected_stage("现世")
	game._enter_current_fight(2)
	for tick in 700:
		game._advance_fight()
		if not game.battle_intro.active:
			break
	for actor: FighterRuntime in [game.naruto, game.ichigo]:
		actor.goto_ai_label("站立", true)
		actor.run_frame_actions()
	game.ichigo.energy = 300
	game.ichigo.source_x = 700
	game.ichigo.source_y = -125
	game.ichigo.set_facing(-1)
	game.naruto.source_x = 100
	game.opponent_driver.timeouts.recorded = true
	game.ichigo.ai_source_state.values.merge({"goran": 0, "hstm": 0, "time": 0,
		"htx": 0, "yup": 0, "tdtime": 50, "touch": false}, true)
	game.opponent_driver.body.beidax(false)
	for child in game.game_world.get_children():
		if child is HitEffectRuntime:
			for tick in 5:
				child.advance_effect()

	await get_tree().process_frame
	print("ESCAPE_FACTION_SMOKE_OK")
	JavaScriptBridge.eval("window.hurtSummonResult = 'passed'")
