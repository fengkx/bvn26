extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fighters: Array[FighterRuntime] = []
	for name in ["minren", "yihu"]:
		var fighter := FighterRuntime.new()
		fighter.fighter_directory = "res://generated/fighters/" + name
		root.add_child(fighter)
		fighters.append(fighter)
	for i in 2:
		var fighter := fighters[i]
		var attacker := fighters[1 - i]
		fighter.opponent = attacker
		fighter.health = 1000
		fighter.energy = 0
		attacker.energy = 0
		attacker.ai_source_state.values["动作"] = 0
		fighter.receive_attack({"damage": 80, "horizontal_impulse": 0,
			"reaction_label": "被打", "vertical_impulse": 0, "hitstun_ms": 700, "impact_strength": 1}, 1)
		fighter.run_frame_actions()
		assert(fighter.health == 1000 and fighter.energy == 0)
		assert(attacker.energy == 0)
		# hitlosehp reads the opponent action at settlement, after receipt.
		attacker.ai_source_state.values["动作"] = 3
		fighter.advance_timeline()
		fighter.run_frame_actions()
		assert(fighter.health == 920 and fighter.energy == 8)
		assert(attacker.energy == 0)
		assert(fighter.hits == 1)
		assert(fighter.ai_source_state.read_field("hits") == 1)
		fighter.run_frame_actions()
		assert(fighter.health == 920 and fighter.hits == 1)
		fighter.goto_ai_label("站立", true)
		assert(fighter.hits == 1)
		fighter.run_frame_actions()
		assert(fighter.hits == 0 and fighter.last_combo_board == 0)
		assert(fighter.ai_source_state.read_field("hits") == 0)
		var body = load("res://generated/fighters/%s/%s/body.gd" % [
			"minren" if i == 0 else "yihu",
			"player_controller" if i == 0 else "ai_controller"]).new({})
		body.adapter = AiBodyContext.new(fighter)
		fighter.source_body = body
		# A cross-up separates facing-from-position from onBeHit's updateDirect(true).
		fighter.position.x = 200
		attacker.position.x = 250
		fighter.set_facing(1)
		attacker.set_facing(1)
		fighter._settle_source_hit(false, false, 1)
		assert(fighter.facing == -1)
		# onDefence uses the same true argument, even after the attacker crosses.
		for direction in [-1, 1]:
			fighter.position.x = 200
			attacker.position.x = 200 + direction * 50
			fighter.set_facing(direction)
			attacker.set_facing(direction)
			fighter.z_index = 7
			attacker.z_index = 9
			var hits_before := fighter.hits
			fighter._settle_source_hit(true, false, 1)
			if fighter.facing != -direction:
				push_error("Source onDefence updateDirect(true) must face opposite the attacker")
				quit(1)
				return
			assert(fighter.hits == hits_before)
			assert(fighter.z_index == 7 and attacker.z_index == 9)
		fighter.source_body = null
		# hitlosehp/onDefence use +=; the later BODY callback owns the cap.
		for defended in [false, true]:
			fighter.z_index = 9
			attacker.z_index = 7
			fighter.health = 1000
			fighter.energy = 299
			attacker.energy = 299
			attacker.ai_source_state.values["动作"] = 0
			fighter.ai_source_state.values["jhp"] = 150
			fighter._settle_source_hit(defended, false, 1)
			assert(fighter.z_index == 7 and attacker.z_index == 9)
			if fighter.energy != (309 if defended else 314) or attacker.energy != (314 if defended else 329):
				push_error("Source hit settlement must retain energy above 300")
				quit(1)
				return
	for fighter in fighters:
		fighter.health = 10
		fighter.ai_source_state.values["jhp"] = 80
		fighter._settle_source_hit(false, true, 1)
		if fighter.health != -70:
			push_error("Source loseHp must retain negative lethal health")
			quit(1)
			return
		fighter.queue_free()
	await process_frame
	print("HIT_SETTLEMENT_FRAME_SMOKE_OK")
	quit()
