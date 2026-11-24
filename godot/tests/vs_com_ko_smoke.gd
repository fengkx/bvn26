extends SceneTree

var mode := 2


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if not args.is_empty(): mode = int(args[0])
	for winning_side in [1, 2]:
		await _run_match(winning_side)
	print("VS_COM_KO_SMOKE_OK")
	quit()


func _run_match(winning_side: int) -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	if mode == 1:
		game._goto_character_selection(1)
		game._on_characters_confirmed(["鸣人", ""], ["我爱罗", ""])
	else:
		game._enter_current_fight(mode)
	game.ichigo.ai_random_clock.cancel()
	for tick in 600:
		game._advance_fight()
		if not game.battle_intro.active:
			break
	assert(not game.battle_intro.active)
	assert(game.ko_state["_root.p1ws"] == 1)
	var loser: FighterRuntime = game.ichigo if winning_side == 1 else game.naruto
	var counter := "_root.p%dws" % winning_side
	var terminal := ("YOUWIN" if winning_side == 1 else "继续") if mode == 1 else "选人画面"
	for round_index in [1, 2]:
		loser.receive_attack({"damage": 2000, "horizontal_impulse": 0,
			"vertical_impulse": 0, "hitstun_ms": 100, "impact_strength": 1, "reaction_label": "被打"}, 1)
		assert(not game.ko_active and not loser.sw)
		for tick in 30:
			game._advance_fight()
			if game.ko_active:
				break
		assert(game.ko_active and loser.sw)
		assert(game.ko_state["_root.焦点"] == loser.player_slot)
		var saw_pause := false
		for tick in 500:
			game._advance_fight()
			if game.ko_paused:
				saw_pause = true
				game._on_hit_fx_resume()
				assert(game.naruto.root_zhanting)
			if game.ko_nextfight_timer != null or game.session.root_label != "游戏场景":
				break
		assert(saw_pause)
		assert(game.ko_state[counter] == round_index + 1)
		assert(game.health_hud.win_frames[winning_side - 1] == round_index + 1)
		if round_index == 1:
			assert(game.ko_nextfight_timer != null and not game.ko_terminal_pending)
			assert(game.ko_nextfight_timer.wait_time == 1.0)
			# Deliver the registered timer callback explicitly in this source fixture.
			game.ko_nextfight_timer.timeout.emit()
			assert(game.ko_state["_root.rounds"] == 2)
			assert(game.naruto.health == game.session.maxhp and game.ichigo.health == game.session.maxhp)
			for tick in 600:
				game._advance_fight()
				if not game.battle_intro.active:
					break
			assert(game.ko_nextfight_timer == null)
			assert(not game.ko_active and not loser.sw)
			assert(game.health_hud.win_frames[winning_side - 1] == 2)
			# Let the ready clip return to its source frame-1 stop before the next KO.
			for tick in 10:
				game._advance_fight()
		else:
			assert(game.session.root_label == terminal and game.opponent_driver == null and game.session.modo == mode)
	await process_frame
	assert(game.session.root_label == terminal)
	assert(game.opponent_driver == null and game.ko_timeline == null)
	assert(game.ko_nextfight_timer == null)
	game.queue_free()
	await process_frame
