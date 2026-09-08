extends SceneTree

const CombatResolverScript = preload("res://combat_resolver.gd")


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fighter_script = load("res://fighter_runtime.gd")
	var naruto: FighterRuntime = fighter_script.new()
	naruto.fighter_directory = "res://generated/fighters/minren"
	root.add_child(naruto)
	await process_frame
	assert(naruto.energy == 0.0)
	assert(naruto.has_command("砍1"))
	assert(naruto.has_command("万解"))
	assert(naruto.has_command("砍4"))
	assert(naruto.command_is_wired("砍1"))
	assert(naruto.command_is_wired("万解"))
	assert(naruto.command_gaps().size() > 0)
	assert(naruto.start_command("万解"))
	assert(naruto.action == "万解")
	naruto.start_action("站立")
	naruto.energy = 300.0
	naruto.enter_frame({"attack": true, "jump": true})
	assert(naruto.action == "万解")
	naruto.start_action("站立")
	naruto.energy = 0.0
	naruto.enter_frame({"attack": true, "jump": true})
	assert(naruto.action == "站立")
	naruto.start_action("站立")

	naruto.position.x = 100.0
	var start_x := naruto.position.x
	naruto.enter_frame({"right": true})
	assert(naruto.action == "走")
	assert(naruto.position.x == start_x + 8.0)
	assert(naruto.facing == 1)
	assert(naruto.current_source_frame() == 10)
	assert(naruto.unnamed_sprite_local_frame(31) == 1)
	naruto.advance_timeline()
	assert(naruto.current_source_frame() == 11)
	assert(naruto.unnamed_sprite_local_frame(31) == 2)
	naruto.advance_timeline()
	assert(naruto.current_source_frame() == 12)
	assert(naruto.unnamed_sprite_local_frame(31) == 3)
	var left_x := naruto.position.x
	naruto.enter_frame({"left": true})
	assert(naruto.action == "走")
	assert(naruto.facing == -1)
	assert(naruto.scale.x < 0.0)
	assert(naruto.position.x == left_x - 8.0)
	naruto.set_facing(1)

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
	var projectile_before := naruto.instance_global_bounds("zh1atm")
	naruto.enter_frame({})
	var projectile_after := naruto.instance_global_bounds("zh1atm")
	assert(is_equal_approx(projectile_after.position.x, projectile_before.position.x + 16.0))
	assert(naruto.instance_clip_frame("zh1atm") == 1)
	naruto.advance_timeline()
	naruto.enter_frame({})
	assert(naruto.instance_clip_frame("zh1atm") == 2)
	naruto.advance_timeline()
	naruto.enter_frame({})
	assert(naruto.instance_clip_frame("zh1atm") == 3)
	naruto.advance_timeline()
	naruto.enter_frame({})
	assert(naruto.instance_clip_frame("zh1atm") == 3)
	var projectile_offset := naruto.instance_local_offset("zh1atm")
	naruto.mark_attack_hit("zh1atm")
	naruto.enter_frame({})
	assert(naruto.instance_local_offset("zh1atm") == projectile_offset)
	assert(naruto.instance_clip_frame("zh1atm") == 5)
	naruto.start_action("站立")
	var rasengan_ground := naruto.position.y
	naruto.configure_stage(rasengan_ground, [])
	var rasengan_x := naruto.position.x
	naruto.enter_frame({"up": true, "ranged": true})
	assert(naruto.action == "招3")
	var rasengan_ticks := 0
	var saw_zh32 := false
	while naruto.action == "招3" and rasengan_ticks < 40:
		if naruto.current_source_frame() >= 486 and naruto.current_source_frame() <= 487:
			var heavy := naruto.active_attack()
			assert(heavy.get("instance_name") == "zh32atm")
			assert(heavy.get("reaction_label") == "击飞")
			assert(float(heavy.get("damage", 0.0)) == 60.0)
			saw_zh32 = true
		naruto.advance_timeline()
		naruto.enter_frame({})
		naruto.run_frame_actions()
		rasengan_ticks += 1
	assert(saw_zh32)
	assert(naruto.action == "落")
	assert(naruto.airborne)
	# 478-484: 7 * 8 * 1.8; 485-490: 6 * 8 * 1.7. Frame 491 exits to 落
	# before that clip's enterFrame, so it must not keep 1.7 through 503.
	assert(is_equal_approx(naruto.position.x, rasengan_x + 182.4))
	naruto.position = Vector2(rasengan_x, rasengan_ground)
	naruto.airborne = false
	naruto.start_action("站立")
	naruto.energy = 100.0
	var summon_energy := naruto.energy
	naruto.enter_frame({"summon": true})
	assert(naruto.action == "招换")
	assert(naruto.energy == summon_energy)
	while naruto.current_source_frame() < 956:
		naruto.advance_timeline()
	naruto.run_frame_actions()
	assert(naruto.energy == summon_energy - 100.0)
	assert(naruto.helper_spawn.get("helper_id") == "我爱罗")
	assert(naruto.helper_spawn.get("start_frame") == 2)
	assert(is_equal_approx(float(naruto.helper_spawn.get("x", 0.0)), naruto.position.x - 20.0))
	var helper_script = load("res://helper_runtime.gd")
	var world_script = load("res://game_world.gd")
	var helper_world: GameWorld = world_script.new()
	var gaara: HelperRuntime = helper_script.new()
	gaara.helper_directory = "res://generated/helpers/woailuo"
	root.add_child(helper_world)
	helper_world.add_child(gaara)
	await process_frame
	gaara.activate(naruto.helper_spawn, naruto)
	assert(gaara.get_parent() == helper_world)
	assert(gaara.helper_id == "我爱罗")
	assert(gaara.attacking)
	assert(gaara.visible)
	assert(gaara.current_source_frame() == 2)
	assert(is_equal_approx(gaara.position.x, naruto.position.x - 20.0 * naruto.facing))
	assert(is_equal_approx(gaara.position.y, naruto.position.y))
	assert(gaara.has_visual_timeline())
	assert(gaara.visual_child_count() > 0)

	# Play path: helper is created at boot (hidden, frame 1 empty), then
	# doZhaoHuan queues helper_spawn and GameWorld activate() shows frame 2.
	var boot_gaara: HelperRuntime = helper_script.new()
	boot_gaara.helper_directory = "res://generated/helpers/woailuo"
	boot_gaara.fighter_directory = "res://generated/helpers/woailuo"
	helper_world.add_child(boot_gaara)
	await process_frame
	assert(not boot_gaara.visible)
	assert(boot_gaara.current_source_frame() == 1)
	assert(boot_gaara.position == Vector2(-200.0, -200.0))
	boot_gaara.activate(naruto.helper_spawn, naruto)
	naruto.helper_spawn = {}
	assert(boot_gaara.visible)
	assert(boot_gaara.attacking)
	assert(boot_gaara.current_source_frame() == 2)
	assert(boot_gaara.has_visual_timeline())
	assert(boot_gaara.visual_child_count() > 0)
	assert(is_equal_approx(boot_gaara.position.x, naruto.position.x - 20.0 * naruto.facing))

	naruto.start_action("站立")
	naruto.enter_frame({"down": true})
	assert(naruto.action == "防御")
	assert(naruto.guarding)
	naruto.advance_timeline()
	naruto.enter_frame({"down": true})
	assert(naruto.action == "防御2")
	assert(naruto.current_source_frame() == 991)
	# onDefence() skill1: hold 下 then 斩. Early return used to ignore J.
	naruto.enter_frame({"down": true, "attack": true})
	assert(naruto.action == "砍技1")
	naruto.start_action("站立")
	naruto.enter_frame({"down": true})
	assert(naruto.action == "防御")
	naruto.advance_timeline()
	naruto.enter_frame({"down": true})
	assert(naruto.action == "防御2")
	assert(naruto.current_source_frame() == 991)
	var guard_health := naruto.health
	var guard_energy := naruto.energy
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
	assert(is_equal_approx(naruto.energy, guard_energy + 2.0))

	# Source fangyu(): zl 15 is encoded as guard-breaking strength 5. Down+J
	# must launch through guard and request the large blue-white XG_mfdjx hit.
	naruto.start_action("防御2")
	naruto.enter_frame({"down": true})
	var break_health := naruto.health
	naruto.receive_attack(
		{
			"damage": 100,
			"impact_strength": 15,
			"horizontal_impulse": 8,
			"vertical_impulse": 1,
			"hitstun_ms": 0,
			"reaction_label": "击飞",
			"instance_name": "kj1atm",
		},
		1
	)
	assert(naruto.health == break_health - 100.0)
	assert(naruto.action == "击飞")
	assert(naruto.last_hit_effect == "XG_mfdjx")
	naruto._launched = false
	naruto._hurt_falling = false
	naruto._hurt_horizontal_step = 0.0
	naruto._hurt_vertical_step = 0.0
	naruto.position.y = naruto._ground_y

	naruto.energy = 0.0
	naruto.start_action("砍技1")
	naruto.advance_timeline()
	naruto.run_frame_actions()
	assert(naruto.energy == 10.0)

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
	naruto.position = Vector2(200.0, 0.0)
	ichigo.position = Vector2(200.0, 0.0)
	naruto.start_action("站立")
	ichigo.start_action("站立")
	naruto.set_facing(1)
	ichigo.set_facing(-1)
	naruto.sync_body_collision_position()
	ichigo.sync_body_collision_position()
	assert(
		naruto.instance_global_bounds("bdmn").intersects(
			ichigo.instance_global_bounds("bdmn")
		)
	)
	CombatResolverScript.resolve_body_pair(naruto, ichigo)
	assert(is_equal_approx(naruto.position.x, 195.0))
	assert(is_equal_approx(ichigo.position.x, 205.0))
	for _tick in range(19):
		CombatResolverScript.resolve_body_pair(naruto, ichigo)
	assert(
		not naruto.instance_global_bounds("bdmn").intersects(
			ichigo.instance_global_bounds("bdmn")
		)
	)
	assert(naruto.position.x < ichigo.position.x)

	# A speed*2 rush must not tunnel through a body between two 30 Hz samples.
	naruto.opponent = ichigo
	ichigo.opponent = naruto
	naruto.position = Vector2(100.0, 0.0)
	ichigo.position = Vector2(0.0, 0.0)
	naruto.set_facing(1)
	ichigo.start_action("站立")
	naruto.start_action("砍技1")
	while naruto.current_source_frame() < 273:
		naruto.advance_timeline()
	var startup_bounds := naruto.instance_global_bounds("kj10atm")
	var target_body := ichigo.instance_global_bounds("bdmn")
	ichigo.position.x += startup_bounds.end.x + 8.0 - target_body.position.x
	assert(not startup_bounds.intersects(ichigo.instance_global_bounds("bdmn")))
	var sweep_start_x := naruto.position.x
	naruto.enter_frame({})
	assert(naruto.action == "砍技12")
	assert(naruto.position.x > sweep_start_x)
	assert(naruto.position.x < sweep_start_x + 16.0)

	naruto.position = Vector2(300.0, 0.0)
	ichigo.position = Vector2(0.0, 0.0)
	naruto.set_facing(-1)
	naruto.start_action("砍技1")
	while naruto.current_source_frame() < 273:
		naruto.advance_timeline()
	startup_bounds = naruto.instance_global_bounds("kj10atm")
	target_body = ichigo.instance_global_bounds("bdmn")
	ichigo.position.x += startup_bounds.position.x - 8.0 - target_body.end.x
	assert(not startup_bounds.intersects(ichigo.instance_global_bounds("bdmn")))
	sweep_start_x = naruto.position.x
	naruto.enter_frame({})
	assert(naruto.action == "砍技12")
	assert(naruto.position.x < sweep_start_x)
	assert(naruto.position.x > sweep_start_x - 16.0)

	# The startup collider only drives the rush. Contact jumps to the original
	# 砍技12 timeline, whose kj1atm owns the damage and finishing artwork.
	naruto.position = Vector2(200.0, 0.0)
	ichigo.position = Vector2(200.0, 0.0)
	naruto.set_facing(1)
	naruto.sync_body_collision_position()
	ichigo.sync_body_collision_position()
	ichigo.start_action("站立")
	naruto.start_action("砍技1")
	while naruto.current_source_frame() < 273:
		naruto.advance_timeline()
	naruto.enter_frame({})
	assert(naruto.action == "砍技12")
	assert(naruto.current_source_frame() == 291)
	var finisher := naruto.attack_contact(ichigo)
	assert(finisher.get("instance_name") == "kj1atm")
	assert(finisher.get("impact_strength") == 15)
	var finisher_health := ichigo.health
	naruto.apply_attack_contact(finisher, ichigo)
	assert(ichigo.health == finisher_health - 100.0)
	assert(ichigo.action == "击飞")
	assert(ichigo.last_hit_effect == "XG_mfdjx")
	var flash_colors: Array[int] = []
	naruto.screen_flash_requested.connect(
		func(color_rgb24: int) -> void: flash_colors.append(color_rgb24)
	)
	naruto.advance_timeline()
	naruto.run_frame_actions()
	naruto.run_frame_actions()
	assert(flash_colors == [1403539])
	ichigo._launched = false
	ichigo._hurt_falling = false
	ichigo._hurt_horizontal_step = 0.0
	ichigo._hurt_vertical_step = 0.0
	ichigo.position.y = ichigo._ground_y
	ichigo.start_action("站立")
	ichigo.set_facing(1)

	ichigo.energy = 300.0
	ichigo.enter_frame({"special": true})
	assert(ichigo.action == "必杀")
	ichigo.advance_timeline()
	ichigo.run_frame_actions()
	assert(ichigo.energy == 200.0)

	ichigo.position.x = 100.0
	ichigo.start_action("招2")
	while ichigo.current_source_frame() < 359:
		ichigo.advance_timeline()
	var rush_x := ichigo.position.x
	ichigo.enter_frame({})
	assert(ichigo.position.x == rush_x + 18.0)

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

	naruto.health = 1000.0
	naruto.position = Vector2(100.0, 0.0)
	naruto.configure_stage(0.0, [])
	naruto.receive_attack(
		{
			"damage": 10,
			"horizontal_impulse": 0,
			"vertical_impulse": 7,
			"hitstun_ms": 0,
			"instance_name": "air_test",
		},
		1
	)
	for _tick in range(40):
		naruto.advance_timeline()
		naruto.enter_frame({})
		naruto.run_frame_actions()
	assert(naruto.position.y == 0.0)
	assert(not naruto.airborne)

	naruto.position = Vector2(100.0, 0.0)
	naruto.configure_stage(0.0, [Rect2(50.0, -30.0, 100.0, 5.0)])
	naruto.start_action("站立")
	naruto.enter_frame({"jump": true})
	for _tick in range(60):
		naruto.advance_timeline()
		naruto.enter_frame({})
		naruto.run_frame_actions()
		if not naruto.airborne:
			break
	assert(naruto.position.y == -30.0)
	assert(not naruto.airborne)
	naruto.start_action("站立")
	naruto.enter_frame({"down": true, "jump": true})
	assert(naruto.action == "落2")
	assert(naruto.airborne)
	for _tick in range(40):
		naruto.advance_timeline()
		naruto.enter_frame({})
		naruto.run_frame_actions()
		if not naruto.airborne:
			break
	assert(naruto.position.y == 0.0)

	naruto.start_action("站立")
	naruto.enter_frame({"down": true, "jump": true})
	# doAllAction evaluates jump after defence on the main floor, so K wins;
	# doDropDown only replaces it with 落2 while standing on a ban.
	assert(naruto.action == "跳")
	naruto.airborne = false

	# 现世 Flash world coords: floorY=-25, ban2 from main.swf frame 现世
	# translate (5, -2073) twips, scaleX 0.3602295, shape width 16500 twips.
	var xianshi_floor := -25.0
	var ban2_x := 5.0 / 20.0
	var ban2_y := -2073.0 / 20.0
	var ban2_w := 16500.0 / 20.0 * 0.3602295
	naruto.position = Vector2(ban2_x + 40.0, xianshi_floor)
	naruto.configure_stage(xianshi_floor, [Rect2(ban2_x, ban2_y, ban2_w, 10.0)])
	naruto.start_action("站立")
	naruto.enter_frame({})
	assert(is_equal_approx(naruto.position.y, xianshi_floor))
	assert(not naruto.airborne)

	naruto.position = Vector2(ban2_x + 40.0, ban2_y)
	naruto.start_action("站立")
	naruto.enter_frame({})
	assert(is_equal_approx(naruto.position.y, ban2_y))
	assert(not naruto.airborne)

	naruto.enter_frame({"down": true})
	assert(naruto.action == "防御")
	naruto.advance_timeline()
	naruto.enter_frame({"down": true})
	assert(naruto.action == "防御2")
	naruto.enter_frame({"down": true, "jump": true})
	assert(naruto.action == "落2")
	assert(naruto.airborne)
	assert(naruto.position.y > ban2_y)
	var past_ban := false
	for _tick in range(40):
		if naruto.position.y > ban2_y + 0.5:
			past_ban = true
		naruto.advance_timeline()
		naruto.enter_frame({})
		naruto.run_frame_actions()
		if not naruto.airborne:
			break
	assert(past_ban)
	assert(is_equal_approx(naruto.position.y, xianshi_floor))
	assert(not naruto.airborne)

	naruto.position = Vector2(200.0, 0.0)
	ichigo.position = Vector2(200.0, 0.0)
	ichigo.start_action("站立")
	naruto.start_action("砍1")
	while naruto.current_source_frame() < 174:
		naruto.advance_timeline()
	assert(naruto.active_attack().get("instance_name") == "k1atm")
	CombatResolverScript.resolve_pair(naruto, ichigo)
	assert(ichigo.action == "被打")
	assert(ichigo.last_event.begins_with("hit_"))

	ichigo.health = 1000.0
	ichigo.start_action("站立")
	naruto.position = Vector2(200.0, 0.0)
	ichigo.position = Vector2(200.0, 0.0)
	naruto.start_action("招3")
	while naruto.current_source_frame() < 486:
		naruto.advance_timeline()
	assert(naruto.active_attack().get("instance_name") == "zh32atm")
	assert(naruto.active_attack().get("reaction_label") == "击飞")
	CombatResolverScript.resolve_pair(naruto, ichigo)
	assert(ichigo.action == "击飞")
	assert(ichigo.last_event == "hit_zh32atm")
	assert(ichigo.last_hit_effect == "XG_qdjx")

	# The sourced up+U sequence must retain contact across both hit windows:
	# zh3 (30, light punch) followed by zh32 (60, heavy launch).
	ichigo.health = 1000.0
	ichigo.position = Vector2(200.0, 0.0)
	ichigo.start_action("站立")
	naruto.position = Vector2(150.0, 0.0)
	naruto.start_action("招3")
	while naruto.current_source_frame() < 488:
		naruto.advance_timeline()
		naruto.enter_frame({})
		ichigo.advance_timeline()
		ichigo.enter_frame({})
		CombatResolverScript.resolve_pair(naruto, ichigo)
		naruto.run_frame_actions()
		ichigo.run_frame_actions()
	assert(is_equal_approx(ichigo.health, 910.0))
	assert(ichigo.action == "击飞")
	assert(ichigo.last_hit_effect == "XG_qdjx")

	ichigo.health = 1000.0
	ichigo.position = Vector2(200.0, 0.0)
	ichigo.configure_stage(0.0, [])
	ichigo.receive_attack(
		{
			"damage": 100,
			"horizontal_impulse": 10,
			"vertical_impulse": 0,
			"hitstun_ms": 0,
			"reaction_label": "击飞",
			"instance_name": "bsatm",
		},
		1
	)
	assert(ichigo.action == "击飞")
	for _tick in range(50):
		ichigo.advance_timeline()
		ichigo.enter_frame({})
		ichigo.run_frame_actions()
	assert(ichigo.position.y == 0.0)
	assert(ichigo.action in ["击落地", "起身", "站立"])

	# Source checkDead(false): hp <= 0 sets sw, KOplay, and gotoAndStop("击飞").
	# 击落地 frame `if(sw == true) stop()` then standup() refuses 起身.
	ichigo.health = 8.0
	ichigo.sw = false
	ichigo.player_slot = "p2"
	ichigo.position = Vector2(200.0, 0.0)
	ichigo.configure_stage(0.0, [])
	ichigo.start_action("站立")
	ichigo.receive_attack(
		{
			"damage": 15,
			"horizontal_impulse": 2,
			"vertical_impulse": 0,
			"hitstun_ms": 300,
			"reaction_label": "被打",
			"instance_name": "k1atm",
		},
		1
	)
	assert(ichigo.health == 0.0)
	assert(ichigo.sw)
	assert(ichigo.action == "击飞")
	assert(ichigo.action != "站立")
	for _tick in range(80):
		ichigo.advance_timeline()
		ichigo.enter_frame({"right": true, "attack": true})
		ichigo.run_frame_actions()
	assert(ichigo.health == 0.0)
	assert(ichigo.sw)
	assert(ichigo.action == "击落地")
	assert(ichigo.action != "站立")
	assert(ichigo.action != "起身")
	assert(ichigo.action != "走")
	var dead_x := ichigo.position.x
	ichigo.enter_frame({"right": true, "left": true, "attack": true, "jump": true})
	assert(ichigo.action == "击落地")
	assert(is_equal_approx(ichigo.position.x, dead_x))

	ichigo.sw = false
	ichigo.health = 1000.0
	ichigo.start_action("站立")

	naruto.opponent = ichigo
	ichigo.opponent = naruto
	naruto.position = Vector2(200.0, 0.0)
	ichigo.position = Vector2(400.0, 0.0)
	gaara.activate(
		{
			"x": naruto.position.x - 20.0,
			"y": naruto.position.y,
			"facing": 1,
			"start_frame": 2,
		},
		naruto
	)
	while gaara.current_source_frame() < 44:
		gaara.advance_timeline()
		gaara.enter_frame()
	assert(gaara.current_source_frame() == 44)
	assert(gaara.instance_global_bounds("atm1").has_area())
	var atm_origin := gaara.instance_placed_origin("atm1")
	assert(
		is_equal_approx(
			gaara.instance_local_offset("atm1").x + atm_origin.x,
			ichigo.position.x - gaara.position.x
		)
	)
	while gaara.attacking:
		gaara.advance_timeline()
		gaara.enter_frame()
	assert(gaara.current_source_frame() == 1)
	assert(not gaara.visible)
	assert(gaara.position == Vector2(-200.0, -200.0))

	var kon: HelperRuntime = helper_script.new()
	kon.helper_directory = "res://generated/helpers/kon"
	root.add_child(kon)
	await process_frame
	ichigo.energy = 100.0
	var drain_energy := ichigo.energy
	kon.activate({"x": 80.0, "y": 0.0, "facing": 1}, naruto)
	assert(kon.attacking)
	assert(kon.helper_id == "魂")
	assert(kon.current_source_frame() == 2)
	assert(kon.attack_contact(ichigo).is_empty())
	while kon.current_source_frame() < 72:
		kon.advance_timeline()
		kon.enter_frame()
	assert(is_equal_approx(ichigo.energy, drain_energy - 20.0))
	while kon.attacking:
		kon.advance_timeline()
		kon.enter_frame()
	assert(kon.current_source_frame() == 1)
	assert(kon.position == Vector2(-200.0, -200.0))

	var close := GameWorld.compute_target(Vector2(400.0, -25.0), Vector2(400.0, -25.0), "all")
	assert(is_equal_approx(float(close["scale"]), 2.0))
	var mid := GameWorld.compute_target(Vector2(100.0, -25.0), Vector2(600.0, -25.0), "all")
	assert(is_equal_approx(float(mid["scale"]), 1.0))
	var far := GameWorld.compute_target(Vector2(20.0, -25.0), Vector2(720.0, -25.0), "all")
	assert(is_equal_approx(float(far["scale"]), 0.8))
	var focus_p1 := GameWorld.compute_target(Vector2(320.0, -25.0), Vector2(650.0, -25.0), "p1")
	assert(is_equal_approx(float(focus_p1["scale"]), 2.0))
	assert(is_equal_approx(float(focus_p1["x"]), -340.0))
	assert(is_equal_approx(float(focus_p1["y"]), 400.0))

	var world: GameWorld = world_script.new()
	root.add_child(world)
	await process_frame
	var left := Node2D.new()
	var right := Node2D.new()
	left.position = Vector2(20.0, -25.0)
	right.position = Vector2(720.0, -25.0)
	world.add_child(left)
	world.add_child(right)
	var locked := world.enter_frame(left, right)
	assert(is_equal_approx(float(locked["lock_min"]), 20.0))
	assert(is_equal_approx(float(locked["lock_max"]), 720.0))
	right.position.x = 800.0
	world.enter_frame(left, right)
	assert(is_equal_approx(right.position.x, 720.0))
	left.position.x = 0.0
	world.enter_frame(left, right)
	assert(is_equal_approx(left.position.x, 20.0))

	var stage_script = load("res://timeline_preview.gd")
	var stage: TimelinePreview = stage_script.new()
	stage.fighter_directory = "res://generated/stages/current_world"
	stage.initial_frame = 2
	stage.autoplay = false
	root.add_child(stage)
	await process_frame
	var ledges := stage.named_instance_ledges("ban")
	assert(ledges.size() == 2)
	assert(is_equal_approx(ledges[0].position.x, 5.0 / 20.0))
	assert(is_equal_approx(ledges[0].position.y, -2073.0 / 20.0))
	assert(is_equal_approx(ledges[1].position.x, 14250.0 / 20.0))
	assert(is_equal_approx(ledges[1].position.y, -2093.0 / 20.0))

	var hit_effect_script = load("res://hit_effect_runtime.gd")
	var hit_effect: HitEffectRuntime = hit_effect_script.new()
	hit_effect.configure("XG_qdjx", Vector2(200.0, -25.0), 1)
	root.add_child(hit_effect)
	await process_frame
	assert(hit_effect.get_child_count() == 1)
	var effect_preview := hit_effect.get_child(0) as TimelinePreview
	assert(effect_preview.current_source_frame() in [1, 2])
	assert(effect_preview.get_child_count() > 0)
	for _tick in range(20):
		await physics_frame
	assert(not is_instance_valid(hit_effect))

	var finisher_effect: HitEffectRuntime = hit_effect_script.new()
	finisher_effect.configure("XG_mfdjx", Vector2(200.0, -25.0), 1)
	root.add_child(finisher_effect)
	await process_frame
	var finisher_preview := finisher_effect.get_child(0) as TimelinePreview
	assert(finisher_preview.get_child_count() > 0)
	for _tick in range(18):
		await physics_frame
	assert(not is_instance_valid(finisher_effect))

	print("COMBAT_SMOKE_OK")
	quit()
