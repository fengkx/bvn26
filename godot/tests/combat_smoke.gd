extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fighter_script = load("res://fighter_runtime.gd")
	var naruto: FighterRuntime = fighter_script.new()
	naruto.fighter_directory = "res://generated/fighters/minren"
	root.add_child(naruto)
	await process_frame

	naruto.position.x = 100.0
	var start_x := naruto.position.x
	naruto.enter_frame({"right": true})
	assert(naruto.action == "走")
	assert(naruto.position.x == start_x + 8.0)

	naruto.start_action("站立")
	naruto.enter_frame({"jump": true})
	assert(naruto.action == "跳")
	assert(naruto.airborne)
	var ground_y := naruto.position.y
	naruto.enter_frame({})
	assert(naruto.position.y == ground_y - 15.0)
	naruto.position.y = ground_y
	naruto.airborne = false

	naruto.start_action("站立")
	naruto.enter_frame({"dash": true})
	assert(naruto.action == "瞬步")
	var dash_x := naruto.position.x
	naruto.enter_frame({})
	assert(naruto.position.x == dash_x + 20.0)
	for _tick in range(10):
		naruto.enter_frame({})

	naruto.start_action("站立")
	naruto.enter_frame({"ranged": true})
	assert(naruto.action == "招1")
	while naruto.current_source_frame() < 382:
		naruto.advance_timeline()
	var ranged_attack := naruto.active_attack()
	assert(ranged_attack.get("instance_name") == "zh1atm")
	assert(float(ranged_attack.get("damage", 0.0)) > 0.0)
	naruto.start_action("站立")
	var summon_energy := naruto.energy
	naruto.enter_frame({"summon": true})
	assert(naruto.action == "招换")
	assert(naruto.energy == summon_energy - 100.0)

	naruto.start_action("站立")
	naruto.enter_frame({"down": true})
	assert(naruto.action == "防御")
	assert(naruto.guarding)
	naruto.advance_timeline()
	naruto.enter_frame({"down": true})
	assert(naruto.action == "防御2")
	assert(naruto.current_source_frame() == 991)
	var guard_health := naruto.health
	naruto.receive_attack(
		{
			"damage": 30,
			"horizontal_impulse": 3,
			"hitstun_ms": 600,
			"instance_name": "k2atm",
		},
		1
	)
	assert(naruto.action == "防住")
	assert(naruto.health == guard_health - 3.0)

	naruto.start_action("砍1")
	while naruto.current_source_frame() < 172:
		naruto.advance_timeline()
	var attack_x := naruto.position.x
	naruto.enter_frame({})
	assert(naruto.position.x == attack_x + 2.0)

	naruto.start_action("砍技1")
	while naruto.current_source_frame() < 273:
		naruto.advance_timeline()
	var skill_x := naruto.position.x
	naruto.enter_frame({})
	assert(naruto.position.x == skill_x + 16.0)

	naruto.start_action("站立")
	naruto.enter_frame({"attack": true})
	assert(naruto.action == "砍1")
	while naruto.current_source_frame() < 176:
		naruto.advance_timeline()
	naruto.enter_frame({"attack": true})
	assert(naruto.action == "砍2")
	while naruto.current_source_frame() < 194:
		naruto.advance_timeline()
	naruto.enter_frame({"attack": true})
	assert(naruto.action == "砍3")

	var hurt_health := naruto.health
	naruto.receive_attack(
		{
			"damage": 15,
			"horizontal_impulse": 2,
			"hitstun_ms": 300,
			"instance_name": "k1atm",
		},
		-1
	)
	assert(naruto.health == hurt_health - 15.0)
	assert(naruto.action == "被打")
	var hurt_x := naruto.position.x
	naruto.enter_frame({})
	assert(naruto.position.x == hurt_x - 2.0)
	while naruto.current_source_frame() < 1020:
		naruto.advance_timeline()
	naruto.run_frame_actions()
	assert(not naruto.timeline_playing)
	for _tick in range(9):
		naruto.enter_frame({})
	assert(naruto.timeline_playing)
	for _tick in range(4):
		naruto.advance_timeline()
		naruto.enter_frame({})
		naruto.run_frame_actions()
	assert(naruto.action == "站立")

	var ichigo: FighterRuntime = fighter_script.new()
	ichigo.fighter_directory = "res://generated/fighters/yihu"
	root.add_child(ichigo)
	await process_frame
	ichigo.enter_frame({"special": true})
	assert(ichigo.action == "必杀")
	assert(ichigo.energy == 200.0)

	naruto.position.x = 200.0
	ichigo.position.x = 200.0
	naruto.energy = 300.0
	naruto.start_action("必杀")
	ichigo.start_action("站立")
	while naruto.current_source_frame() < 531:
		naruto.advance_timeline()
	assert(ichigo.incoming_attack_hits(naruto))
	while naruto.current_source_frame() < 538:
		naruto.advance_timeline()
	naruto.run_frame_actions()
	assert(naruto.action == "必杀1")

	naruto.position.x = 200.0
	ichigo.position.x = 200.0
	naruto.energy = 0.0
	naruto.start_action("砍1")
	ichigo.start_action("站立")
	while naruto.current_source_frame() < 174:
		naruto.advance_timeline()
	assert(naruto.instance_global_bounds("k1atm").has_area())
	assert(ichigo.instance_global_bounds("bdmn").has_area())
	assert(ichigo.incoming_attack_hits(naruto))
	assert(naruto.energy == 3.0)

	naruto.health = 199.0
	naruto.energy = 0.0
	naruto.enter_frame({})
	assert(is_equal_approx(naruto.energy, 0.2))

	print("COMBAT_SMOKE_OK")
	quit()
