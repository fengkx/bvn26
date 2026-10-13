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
	# The standalone fixture must run the source load before child load callbacks.
	naruto.ai_source_state.apply_load()
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
	# 跳 starts at 40; clip is placed at 42; enterFrame starts at 43.
	naruto.enter_frame({})
	assert(is_equal_approx(naruto.position.y, ground_y))
	naruto.advance_timeline()
	naruto.enter_frame({})
	naruto.advance_timeline()
	naruto.enter_frame({})
	assert(is_equal_approx(naruto.position.y, ground_y))
	naruto.advance_timeline()
	naruto.enter_frame({})
	assert(is_equal_approx(naruto.position.y, ground_y - 14.0))
	naruto.position.y = ground_y
	naruto.airborne = false

	# DefineSprite_764/frame_42 StartSound soundId=40.
	naruto.start_action("跳")
	while naruto.current_source_frame() < 42:
		naruto.advance_timeline()
	assert(naruto.current_source_frame() == 42)
	assert(40 in naruto.last_sound_ids)
	naruto.start_action("站立")
	naruto.position.y = ground_y
	naruto.airborne = false

	naruto.start_action("站立")
	naruto.enter_frame({"dash": true})
	assert(naruto.action == "瞬步")
	while naruto.current_source_frame() < 21:
		naruto.advance_timeline()
	var dash_x := naruto.position.x
	naruto.enter_frame({})
	assert(naruto.position.x == dash_x + 20.0)
	naruto.energy = 100.0
	naruto.enter_frame({"special": true})
	assert(naruto.action == "必杀")
	naruto.start_action("落地")
	while naruto.current_source_frame() < 116:
		naruto.advance_timeline()
	naruto.enter_frame({"attack": true})
	assert(naruto.action == "砍1")
	naruto.start_action("砍3")
	while naruto.current_source_frame() < 217:
		naruto.advance_timeline()
	naruto.enter_frame({"attack": true})
	assert(naruto.action == "砍4")
	naruto.configure_stage(0.0, [])
	naruto.position.y = 0.0
	naruto.start_action("超必杀2")
	while naruto.current_source_frame() < 942:
		naruto.advance_timeline()
	naruto.enter_frame({})
	assert(naruto.action == "击飞")
	# Source 942 sets yup/htx then 击飞; beidax lands to 击落地. Do not
	# wipe _hurt_falling here — that hid the stuck-in-击飞 bug.
	for _tick in range(80):
		naruto.advance_timeline()
		naruto.enter_frame({})
		naruto.run_frame_actions()
		if naruto.action in ["击落地", "起身", "站立"]:
			break
	assert(naruto.action in ["击落地", "起身", "站立"])
	naruto._launched = false
	naruto._hurt_falling = false
	naruto.position.y = naruto._ground_y
	naruto.start_action("站立")
	naruto.enter_frame({"down": true, "attack": true, "ranged": true})
	# doAllAction first leaving goto is defence() → 防御.
	# Source: DefineSprite_16/frame_1/DoAction.as doAllAction.
	assert(naruto.action == "防御")
	naruto.enter_frame({"down": true, "attack": true, "ranged": true})
	# onDefence later goto: magichit2 after skill1 / 防御2 pin.
	assert(naruto.action == "招2")
	naruto.energy = 100.0
	naruto.start_action("站立")
	naruto.enter_frame({"up": true, "special": true})
	# bishaUP before bisha; first leaving goto from 站立 is 上必杀.
	assert(naruto.action == "上必杀")
	naruto.start_action("击落地")
	while naruto.current_source_frame() < 1039:
		naruto.advance_timeline()
	naruto.enter_frame({"dash": true})
	# 击落地 clip standup() → 起身. Source: DefineSprite_764/frame_1039.
	assert(naruto.action == "起身")
	naruto.start_action("击落地")
	while naruto.current_source_frame() < 1069:
		naruto.advance_timeline()
	naruto.enter_frame({})
	# Unconditional gotoAndStop("站立") at 1069, not 起身.
	assert(naruto.action == "站立")

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
	# Receiver settlement alone cannot satisfy the child's source hitTest.
	assert(naruto.instance_local_offset("zh1atm").x == projectile_offset.x + 16.0)
	assert(naruto.instance_clip_frame("zh1atm") == 3)
	var projectile_target: FighterRuntime = fighter_script.new()
	projectile_target.fighter_directory = "res://generated/fighters/yihu"
	root.add_child(projectile_target)
	await process_frame
	naruto.opponent = projectile_target
	projectile_target.position += naruto.instance_global_bounds("zh1atm").get_center() - projectile_target.instance_global_bounds("bdmn").get_center()
	projectile_offset = naruto.instance_local_offset("zh1atm")
	naruto.enter_frame({})
	assert(naruto.instance_local_offset("zh1atm") == projectile_offset)
	assert(naruto.instance_clip_frame("zh1atm") == 5)
	naruto.opponent = null
	projectile_target.queue_free()
	naruto.start_action("站立")
	var rasengan_ground := naruto.position.y
	naruto.configure_stage(rasengan_ground, [])
	var rasengan_x := naruto.position.x
	naruto.enter_frame({"up": true, "ranged": true})
	# doAllAction: magichit3 before magichit1; 站立 helper is removed on 招3.
	assert(naruto.action == "招3")
	# continue the sourced 招3 clip already entered from 上+招
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
	# Source: DefineSprite_764/frame_1003/DoAction.as calls onDefence(2).
	naruto.run_frame_actions()
	naruto.advance_timeline()
	naruto.run_frame_actions()
	assert(naruto.health == guard_health - 3.0)
	assert(is_equal_approx(naruto.energy, guard_energy + 2.0))
	assert(naruto.hits == 0)
	assert(naruto.last_combo_board == 0)

	# Source fangyu(): zl <= 10 stays on 防住 and plays bdfyxg, no hits++.
	naruto.start_action("防御2")
	naruto.enter_frame({"down": true})
	var blocked_hits := naruto.hits
	naruto.receive_attack(
		{
			"damage": 15,
			"impact_strength": 2,
			"horizontal_impulse": 2,
			"hitstun_ms": 300,
			"instance_name": "k1atm",
		},
		1
	)
	assert(naruto.action == "防住")
	naruto.run_frame_actions()
	naruto.advance_timeline()
	naruto.run_frame_actions()
	assert(naruto.hits == blocked_hits)
	assert(naruto.last_hit_effect == "XG_fyq")
	assert(naruto.last_combo_board == 0)

	# Source bdfyxg() case 1: a blocked 斩 (zl=1) plays XG_fykan, the blue
	# blade burst, not the XG_fyq ring.
	naruto.start_action("防御2")
	naruto.enter_frame({"down": true})
	naruto.receive_attack(
		{
			"damage": 10,
			"impact_strength": 1,
			"horizontal_impulse": 2,
			"hitstun_ms": 300,
			"instance_name": "k1atm",
		},
		1
	)
	assert(naruto.action == "防住")
	naruto.run_frame_actions()
	naruto.advance_timeline()
	naruto.run_frame_actions()
	assert(naruto.hits == blocked_hits)
	# Source frame1003 uses onDefence(2), so bdfyxg2 maps zl=1 to XG_fyq.
	assert(naruto.last_hit_effect == "XG_fyq")

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
	naruto.run_frame_actions()
	naruto.advance_timeline()
	naruto.run_frame_actions()
	assert(naruto.health == break_health - 100.0)
	assert(naruto.action == "击飞")
	# Source onBeHit(true) is the flying branch; it has no ordinary onBeHit0 effect event.
	assert(naruto.hits == blocked_hits + 1)
	assert(naruto.last_combo_board == 0)
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
	naruto.run_frame_actions()
	assert(naruto.health == hurt_health)
	assert(naruto.action == "被打")
	var hurt_x := naruto.position.x
	# Source onBeHit settles at frame1015; its PlaceObject enterFrame starts at frame1017.
	naruto.advance_timeline()
	naruto.run_frame_actions()
	assert(naruto.health == hurt_health - 15.0)
	while naruto.current_source_frame() < 1017:
		naruto.advance_timeline()
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
	# Drain initial frame-1 scripts before injecting a later source hit.
	ichigo.run_frame_actions()
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
	ichigo.run_frame_actions()
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
	# Drain any prior source-frame queue before injecting a new receiver packet.
	ichigo.run_frame_actions()
	naruto.apply_attack_contact(finisher, ichigo)
	# Source DefineSprite_638/frame_752/DoAction.as settles the flying hit after the queued entry frame.
	ichigo.run_frame_actions()
	ichigo.advance_timeline()
	ichigo.run_frame_actions()
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

	# 砍技1 has no gotoAndStop. The playhead continues into 砍技12 even
	# when kj10atm never touches bdmn; contact is only an early explode.
	naruto.position = Vector2(40.0, 0.0)
	ichigo.position = Vector2(400.0, 0.0)
	naruto.set_facing(1)
	ichigo.start_action("站立")
	naruto.start_action("砍技1")
	while naruto.action == "砍技1":
		naruto.enter_frame({})
		if naruto.action != "砍技1":
			break
		naruto.advance_timeline()
	assert(naruto.action == "砍技12")
	assert(naruto.current_source_frame() == 291)
	var whiff_flash: Array[int] = []
	naruto.screen_flash_requested.connect(
		func(color_rgb24: int) -> void: whiff_flash.append(color_rgb24)
	)
	while naruto.action == "砍技12" and naruto.current_source_frame() < 313:
		naruto.advance_timeline()
		naruto.enter_frame({})
		naruto.run_frame_actions()
	assert(whiff_flash == [1403539])
	assert(naruto.action == "站立")

	ichigo._launched = false
	ichigo._hurt_falling = false
	ichigo._hurt_horizontal_step = 0.0
	ichigo._hurt_vertical_step = 0.0
	ichigo.position.y = ichigo._ground_y
	ichigo.start_action("站立")
	ichigo.set_facing(1)

	ichigo.start_action("砍技1")
	while ichigo.current_source_frame() < 278:
		ichigo.advance_timeline()
	ichigo.enter_frame({})
	assert(ichigo.action == "站立")
	ichigo.start_action("砍1")
	ichigo.energy = 300.0
	while ichigo.current_source_frame() < 173:
		ichigo.advance_timeline()
	ichigo.enter_frame({"attack": true, "jump": true})
	assert(ichigo.action == "万解")
	ichigo.start_action("站立")
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
	# Source DefineSprite_638/frame_739/DoAction.as settles the receiver packet on its next frame.
	ichigo.advance_timeline()
	ichigo.run_frame_actions()
	# The source attacker is in action state 3 here, so its opponent-energy branch is skipped.
	assert(naruto.energy == 0.0)

	# Flash MATRIX / JPEXS Matrix.transform on DefineSprite_2 (0,0)-(1319,810)
	# twips. yihu 上必杀 sbsatm@548 is a 90° box: scale=0, rotateSkew0=-1.1421814,
	# rotateSkew1=3.7250671. Swapping the skews turns this into a tall strip
	# behind the attacker; source AABB is a wide slash in front.
	# Source: scripts/fighter/yihu.json getHitObj() + timeline frame 548.
	ichigo.health = 1000.0
	ichigo.hits = 0
	ichigo.sw = false
	ichigo.position = Vector2(250.0, 0.0)
	ichigo.start_action("站立")
	ichigo.set_facing(-1)
	ichigo.energy = 100.0
	ichigo.start_action("上必杀")
	while ichigo.current_source_frame() < 548:
		ichigo.advance_timeline()
	assert(ichigo.current_source_frame() == 548)
	var sbs_local := ichigo.instance_local_bounds("sbsatm")
	assert(sbs_local.has_area())
	assert(sbs_local.size.x > 140.0)
	assert(sbs_local.size.y < 90.0)
	assert(sbs_local.end.x > 40.0)
	naruto.health = 1000.0
	naruto.hits = 0
	naruto.sw = false
	naruto.position = Vector2(200.0, 0.0)
	naruto.start_action("站立")
	naruto.set_facing(1)
	assert(naruto.incoming_attack_hits(ichigo))
	assert(naruto.action == "击飞")
	# Source DefineSprite_638/frame_752/DoAction.as settles the flying hit on the queued next frame.
	naruto.advance_timeline()
	naruto.run_frame_actions()
	assert(naruto.hits == 1)
	assert(is_equal_approx(naruto.health, 750.0))
	# Source onBeHit(true) is the flying branch; it has no ordinary onBeHit0 effect event.

	# yihu 超必杀 cbsatm@606: same rotated DefineSprite_2 convention.
	naruto.health = 1000.0
	naruto.hits = 0
	naruto.sw = false
	naruto._launched = false
	naruto._hurt_falling = false
	naruto.position = Vector2(200.0, 0.0)
	naruto.start_action("站立")
	ichigo.health = 1000.0
	ichigo.energy = 300.0
	ichigo.position = Vector2(250.0, 0.0)
	ichigo.start_action("超必杀")
	while ichigo.current_source_frame() < 606:
		ichigo.advance_timeline()
	assert(ichigo.current_source_frame() == 606)
	var cbs_local := ichigo.instance_local_bounds("cbsatm")
	assert(cbs_local.has_area())
	assert(cbs_local.size.x > 90.0)
	assert(cbs_local.end.x > 40.0)
	assert(naruto.incoming_attack_hits(ichigo))
	assert(naruto.action == "击飞")
	# Source flying-hit settlement is queued after the receiver enters its hit timeline.
	naruto.advance_timeline()
	naruto.run_frame_actions()
	assert(is_equal_approx(naruto.health, 550.0))

	# minren 超必杀2 cbs3atm@904 then a new PlaceObject cbsatm@932.
	# getHitObj() has no already-hit flag; a later PlaceObject can connect.
	naruto.health = 1000.0
	naruto.hits = 0
	naruto.sw = false
	naruto._launched = false
	naruto._hurt_falling = false
	naruto.energy = 300.0
	naruto.position = Vector2(200.0, 0.0)
	naruto.set_facing(1)
	naruto.start_action("超必杀2")
	ichigo.health = 1000.0
	ichigo.hits = 0
	ichigo.sw = false
	ichigo._launched = false
	ichigo._hurt_falling = false
	ichigo.position = Vector2(250.0, 0.0)
	ichigo.start_action("站立")
	while naruto.current_source_frame() < 904:
		naruto.advance_timeline()
	assert(naruto.current_source_frame() == 904)
	var cbs3_local := naruto.instance_local_bounds("cbs3atm")
	assert(cbs3_local.has_area())
	assert(cbs3_local.size.x > 140.0)
	assert(cbs3_local.end.x > 40.0)
	assert(ichigo.incoming_attack_hits(naruto))
	assert(ichigo.action == "被打")
	# Source DefineSprite_1180/frame_919/DoAction.as settles the normal hit on the next receiver frame.
	ichigo.advance_timeline()
	ichigo.run_frame_actions()
	assert(ichigo.hits == 1)
	assert(is_equal_approx(ichigo.health, 970.0))
	ichigo.start_action("站立")
	ichigo.hits = 1
	while naruto.current_source_frame() < 932:
		naruto.advance_timeline()
	assert(naruto.current_source_frame() == 932)
	assert(ichigo.incoming_attack_hits(naruto))
	assert(ichigo.action == "击飞")
	# Source DefineSprite_1180/frame_932/DoAction.as settles the flying hit on the next receiver frame.
	ichigo.advance_timeline()
	ichigo.run_frame_actions()
	assert(is_equal_approx(ichigo.health, 770.0))

	# Source DefineSprite_764/frame_832/DoAction.as copies wrapper _x only.
	# Same ground plane: after the flash, cbs1atm@837 can hit. A defender
	# at jump height keeps its Y, so that *atm misses. Do not enlarge boxes.
	# frame_884 then writes _x, _y-40, and jump=1.
	naruto.health = 1000.0
	naruto.hits = 0
	naruto.sw = false
	naruto._launched = false
	naruto._hurt_falling = false
	naruto.energy = 300.0
	naruto.position = Vector2(150.0, 0.0)
	naruto.set_facing(1)
	ichigo.health = 1000.0
	ichigo.hits = 0
	ichigo.sw = false
	ichigo._launched = false
	ichigo._hurt_falling = false
	ichigo.position = Vector2(400.0, 0.0)
	ichigo.start_action("站立")
	naruto.start_action("超必杀")
	while naruto.current_source_frame() < 832:
		naruto.advance_timeline()
	assert(naruto.current_source_frame() == 832)
	naruto.enter_frame({})
	naruto.run_frame_actions()
	assert(is_equal_approx(naruto.position.x, ichigo.position.x))
	assert(is_equal_approx(naruto.position.y, 0.0))
	while naruto.current_source_frame() < 837:
		naruto.advance_timeline()
		naruto.enter_frame({})
		naruto.run_frame_actions()
	assert(naruto.current_source_frame() == 837)
	assert(naruto.instance_global_bounds("cbs1atm").has_area())
	assert(ichigo.incoming_attack_hits(naruto))
	# Source receiver frame settles this contact on the next yihu timeline frame.
	ichigo.advance_timeline()
	ichigo.run_frame_actions()
	assert(ichigo.hits == 1)

	ichigo.start_action("站立")
	ichigo.health = 1000.0
	ichigo.hits = 0
	ichigo.position = Vector2(400.0, -80.0)
	naruto.position = Vector2(150.0, 0.0)
	naruto.energy = 300.0
	naruto.start_action("超必杀")
	while naruto.current_source_frame() < 832:
		naruto.advance_timeline()
	naruto.enter_frame({})
	naruto.run_frame_actions()
	assert(is_equal_approx(naruto.position.x, 400.0))
	assert(is_equal_approx(naruto.position.y, 0.0))
	while naruto.current_source_frame() < 837:
		naruto.advance_timeline()
		naruto.enter_frame({})
		naruto.run_frame_actions()
	assert(naruto.current_source_frame() == 837)
	assert(naruto.attack_contact(ichigo).is_empty())
	assert(ichigo.action == "站立")
	assert(ichigo.hits == 0)

	ichigo.position = Vector2(400.0, 0.0)
	naruto.position = Vector2(150.0, 0.0)
	naruto.energy = 300.0
	naruto.start_action("超必杀")
	while naruto.current_source_frame() < 884:
		naruto.advance_timeline()
		naruto.enter_frame({})
		naruto.run_frame_actions()
	assert(naruto.current_source_frame() == 884)
	assert(is_equal_approx(naruto.position.x, 400.0))
	assert(is_equal_approx(naruto.position.y, -40.0))
	assert(naruto.action == "超必杀")

	# Full 下+I: beidax 被打 has no zhongli, so cbs2 yup keeps the defender
	# up. 884 warps the attacker to opponent.y-40. cbsatm@932 is 击飞.
	# Source: DefineSprite_764/frame_832,884,886,942 and gjl cbs/cbs2.
	ichigo.health = 1000.0
	ichigo.hits = 0
	ichigo.sw = false
	ichigo._launched = false
	ichigo._hurt_falling = false
	ichigo.position = Vector2(400.0, 0.0)
	ichigo.start_action("站立")
	naruto.position = Vector2(150.0, 0.0)
	naruto.energy = 300.0
	naruto.start_action("超必杀")
	var saw_cbs2_hover := false
	var saw_warp_to_hover := false
	var saw_cbs_launch := false
	var saw_cbs_contact := false
	for _tick in range(200):
		naruto.advance_timeline()
		ichigo.advance_timeline()
		naruto.enter_frame({})
		ichigo.enter_frame({})
		CombatResolverScript.resolve_body_pair(naruto, ichigo)
		var cbs_hit_before := naruto._hit_instances.has("cbsatm")
		CombatResolverScript.resolve_pair(naruto, ichigo)
		# Bind identity to the resolver's accepted packet: resolve_pair marks the actual source instance.
		if not cbs_hit_before and naruto._hit_instances.has("cbsatm"):
			saw_cbs_contact = true
		naruto.run_frame_actions()
		ichigo.run_frame_actions()
		if (
			naruto.current_source_frame() >= 861
			and naruto.current_source_frame() < 884
			and naruto.action == "超必杀"
			and ichigo.position.y < -80.0
		):
			saw_cbs2_hover = true
		if (
			naruto.action == "超必杀"
			and naruto.current_source_frame() == 884
			and ichigo.position.y < -40.0
			and is_equal_approx(naruto.position.x, ichigo.position.x)
			and is_equal_approx(naruto.position.y, ichigo.position.y - 40.0)
		):
			saw_warp_to_hover = true
		# Preserve the source cbsatm packet identity across the receiver-frame settlement.
		if saw_cbs_contact and ichigo.action == "击飞" and ichigo.hits > 0:
			saw_cbs_launch = true
			break
	assert(saw_cbs2_hover)
	assert(saw_warp_to_hover)
	assert(saw_cbs_launch)
	naruto.start_action("站立")
	naruto.position = Vector2(200.0, 0.0)
	naruto.energy = 0.0
	ichigo.health = 1000.0
	ichigo.hits = 0
	ichigo.position = Vector2(200.0, 0.0)
	ichigo.start_action("站立")

	# Facing / bdmn warps are on yihu DefineSprite_1672 (招3@442, 上必杀@555),
	# not the current 638 slice. Lock the interpreter only.
	var original_combat: Dictionary = ichigo._combat
	var warp_combat: Dictionary = ichigo._combat.duplicate(true)
	warp_combat["body_warps"] = [
		{
			"action": "招3",
			"frame": 442,
			"op": "warp_to_opponent",
			"place_x": true,
			"place_y": true,
			"xscale_gt_0": {"set_xscale": -100.0, "x_pixels": 100.0},
			"xscale_lt_0": {"set_xscale": 100.0, "x_pixels": -100.0},
		},
		{
			"action": "上必杀",
			"frame": 555,
			"op": "warp_to_opponent",
			"place_x": true,
			"place_y": true,
			"xscale_gt_0": {"set_xscale": -100.0, "x_bdmn_width": -0.7},
			"xscale_lt_0": {"set_xscale": 100.0, "x_bdmn_width": 0.7},
			"y_bdmn_height": 0.5,
		},
	]
	ichigo._combat = warp_combat
	naruto.position = Vector2(400.0, 0.0)
	naruto.start_action("站立")
	ichigo.position = Vector2(150.0, 0.0)
	ichigo.set_facing(1)
	ichigo.start_action("招3")
	while ichigo.current_source_frame() < 442:
		ichigo.advance_timeline()
	assert(ichigo.current_source_frame() == 442)
	ichigo.root_zhanting = true
	ichigo.enter_frame({})
	assert(ichigo.facing == 1 and ichigo.scale.x == -1.0)
	assert(is_equal_approx(ichigo.position.x, 500.0))
	assert(is_equal_approx(ichigo.position.y, 0.0))
	ichigo.set_facing(-1)
	ichigo.position = Vector2(150.0, 0.0)
	# Reset the prior source frame-442 queue before replaying the opposite facing branch.
	ichigo.start_action("站立")
	ichigo.run_frame_actions()
	ichigo.start_action("招3")
	while ichigo.current_source_frame() < 442:
		ichigo.advance_timeline()
	ichigo.root_zhanting = true
	ichigo.enter_frame({})
	assert(ichigo.facing == -1 and ichigo.scale.x == 1.0)
	assert(is_equal_approx(ichigo.position.x, 300.0))
	# Repeating the warp branches on MovieClip._xscale, not unchanged scale_X.
	ichigo._apply_body_warp_event(warp_combat["body_warps"][0], 1001)
	assert(ichigo.facing == -1 and ichigo.scale.x == -1.0)
	assert(is_equal_approx(ichigo.position.x, 500.0))
	ichigo.root_zhanting = false
	var stand_body := naruto.instance_global_bounds("bdmn")
	assert(stand_body.has_area())
	ichigo.set_facing(1)
	ichigo.position = Vector2(150.0, 0.0)
	ichigo.start_action("上必杀")
	while ichigo.current_source_frame() < 555:
		ichigo.advance_timeline()
	assert(ichigo.current_source_frame() == 555)
	ichigo.root_zhanting = true
	ichigo.enter_frame({})
	var stand_body_local := naruto.instance_local_bounds("bdmn")
	assert(ichigo.facing == 1 and ichigo.scale.x == -1.0)
	# Source MATRIX uses the raw local bounds, then Flash rounds the written coordinates to twips.
	var expected_warp_x := roundf((naruto.position.x - stand_body_local.size.x * 0.7) * 20.0) / 20.0
	var expected_warp_y := roundf((naruto.position.y + stand_body_local.size.y * 0.5) * 20.0) / 20.0
	assert(is_equal_approx(ichigo.position.x, expected_warp_x))
	assert(is_equal_approx(ichigo.position.y, expected_warp_y))
	ichigo.root_zhanting = false
	ichigo._combat = original_combat
	ichigo.position = Vector2(200.0, 0.0)
	ichigo.start_action("站立")
	naruto.position = Vector2(200.0, 0.0)

	# minren 砍技2: kj21atm is a new PlaceObject at 331 and again at 338.
	# Source getHitObj() can connect both windows after the first clip leaves.
	naruto.start_action("站立")
	naruto.position = Vector2(200.0, 0.0)
	naruto.set_facing(1)
	naruto.start_action("砍技2")
	ichigo.health = 1000.0
	ichigo.hits = 0
	ichigo.sw = false
	ichigo._launched = false
	ichigo._hurt_falling = false
	ichigo.position = Vector2(200.0, 0.0)
	ichigo.start_action("站立")
	while naruto.current_source_frame() < 331:
		naruto.advance_timeline()
	assert(naruto.current_source_frame() == 331)
	assert(ichigo.incoming_attack_hits(naruto))
	# Source DefineSprite_1180/frame_739/DoAction.as settles this queued hit on the next receiver frame.
	ichigo.advance_timeline()
	ichigo.run_frame_actions()
	assert(ichigo.hits == 1)
	var after_first_kj21 := ichigo.health
	ichigo.start_action("站立")
	# Source 站立 frame 1 reinitializes beida/hited before the repeat contact.
	ichigo.run_frame_actions()
	ichigo.hits = 1
	while naruto.current_source_frame() < 338:
		naruto.advance_timeline()
	assert(naruto.current_source_frame() == 338)
	assert(ichigo.incoming_attack_hits(naruto))
	ichigo.advance_timeline()
	ichigo.run_frame_actions()
	assert(ichigo.hits == 2)
	assert(ichigo.health < after_first_kj21)
	ichigo.energy = 0.0
	ichigo.hits = 0
	ichigo.sw = false
	ichigo._launched = false
	ichigo._hurt_falling = false
	ichigo.start_action("站立")
	naruto.energy = 0.0
	naruto.hits = 0
	naruto.start_action("站立")

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

	# enterFrame skips the PlaceObject frame; step 2 is a new clip so js=0.
	# 14+13+12+11+10+9+8 = 77. Wrapper `_y` is the player clip, not mc.
	naruto.position = Vector2(80.0, 0.0)
	naruto.configure_stage(0.0, [])
	naruto.start_action("站立")
	assert(is_equal_approx(naruto.wrapper_translation().y, -478.0 / 20.0))
	naruto.enter_frame({"jump": true})
	var apex := naruto.position.y
	for _tick in range(20):
		naruto.advance_timeline()
		naruto.enter_frame({})
		naruto.run_frame_actions()
		apex = minf(apex, naruto.position.y)
		if naruto.action == "落":
			break
	assert(is_equal_approx(apex, -77.0))
	assert(naruto.action == "落")

	naruto.position = Vector2(100.0, -30.0)
	naruto.configure_stage(0.0, [Rect2(50.0, -30.0, 100.0, 5.0)])
	naruto.airborne = false
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
	# doAllAction first leaving goto is defence(); jump() is later and does
	# not run after the 站立 helper is removed. Drop-through is only
	# doDropDown while standing on a ban, handled before catalog dispatch.
	assert(naruto.action == "防御")
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
	naruto.enter_frame({"jump": true})
	var jump_apex := naruto.position.y
	for _tick in range(40):
		naruto.advance_timeline()
		naruto.enter_frame({})
		naruto.run_frame_actions()
		jump_apex = minf(jump_apex, naruto.position.y)
		if not naruto.airborne:
			break
	assert(jump_apex > ban2_y)
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
	# Source receiver dispatch emits the reaction action event after hit_received is consumed.
	assert(ichigo.last_event == "action_被打")

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
	# The source hit is observable through the queued reaction action; diagnostic last_event is action-scoped.
	assert(ichigo.last_event == "action_击飞")
	ichigo.advance_timeline()
	ichigo.run_frame_actions()
	# Source DefineSprite_1180/frame_800/DoAction.as uses onBeHit(true); flying hits have no ordinary effect event.

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

	# SOP D: hits++ only in onBeHit; HUD only when hits > 1; 站立 frame 2
	# clears; bar2 chases only after that at maxhp/500.
	naruto.player_slot = "p1"
	ichigo.player_slot = "p2"
	ichigo.hits = 0
	ichigo.last_combo_board = 0
	ichigo.health = 1000.0
	ichigo.displayed_health = 1000.0
	ichigo.max_health = 1000.0
	ichigo.start_action("被打")
	ichigo.receive_attack(
		{
			"damage": 15,
			"impact_strength": 2,
			"horizontal_impulse": 2,
			"hitstun_ms": 300,
			"reaction_label": "被打",
			"instance_name": "k1atm",
		},
		1
	)
	ichigo.advance_timeline()
	ichigo.run_frame_actions()
	assert(ichigo.hits == 1)
	assert(ichigo.last_combo_board == 0)
	ichigo.run_frame_actions()
	assert(is_equal_approx(ichigo.displayed_health, 1000.0))
	ichigo.receive_attack(
		{
			"damage": 15,
			"impact_strength": 2,
			"horizontal_impulse": 2,
			"hitstun_ms": 300,
			"reaction_label": "被打",
			"instance_name": "k1atm",
		},
		1
	)
	ichigo.advance_timeline()
	ichigo.run_frame_actions()
	assert(ichigo.hits == 2)
	assert(ichigo.last_combo_board == 1)
	ichigo.run_frame_actions()
	assert(is_equal_approx(ichigo.displayed_health, 1000.0))
	var hud_script = load("res://combo_hud.gd")
	var hud: ComboHud = hud_script.new()
	root.add_child(hud)
	hud.load_spec("res://generated/main/hit_receive.json")
	hud.play(1, 2)
	assert(not hud.showing(1))
	hud.tick()
	assert(hud.showing(1))
	assert(hud.displayed_hits(1) == 2)
	assert(not hud.showing(2))
	ichigo.start_action("站立")
	assert(ichigo.hits == 2)
	ichigo.enter_frame({})
	assert(ichigo.hits == 2)
	assert(ichigo.current_source_frame() == 1)
	ichigo.advance_timeline()
	ichigo.enter_frame({})
	assert(ichigo.current_source_frame() == 2)
	ichigo.run_frame_actions()
	# DefineSprite_1180/frame_2/DoAction.as resets hits when its source script executes.
	assert(ichigo.hits == 0)
	assert(is_equal_approx(ichigo.displayed_health, 998.0))

	# Source bsd@507: _root.zhanting, shine, blackStg, stopMc(opponent),
	# showFace(pn,"鸣人2") on face_p1.
	var super_presentation_script = load("res://super_presentation.gd")
	var super_runtime_script = load("res://super_runtime.gd")
	var presentation = super_presentation_script.new()
	presentation.load_spec("res://generated/main/hit_receive.json")
	var director = super_runtime_script.new()
	director.presentation = presentation
	naruto.player_slot = "p1"
	ichigo.player_slot = "p2"
	naruto.opponent = ichigo
	ichigo.opponent = naruto
	naruto.super_runtime = director
	ichigo.super_runtime = director
	ichigo.start_action("站立")
	ichigo.timeline_playing = true
	var ichigo_frame := ichigo.current_source_frame()
	naruto.airborne = false
	naruto.position.y = naruto._ground_y
	naruto.start_action("必杀")
	for _tick in range(10):
		if naruto.current_source_frame() >= 507 and naruto.action == "必杀":
			break
		naruto.advance_timeline()
	assert(naruto.action == "必杀")
	assert(naruto.current_source_frame() == 507)
	naruto.enter_frame({})
	assert(naruto.action == "必杀")
	assert(naruto.zhanting)
	assert(naruto.bs == 1)
	assert(director.zhanting)
	assert(ichigo.root_zhanting)
	assert(not ichigo.timeline_playing)
	assert(not presentation.bgmc_visible)
	assert(not presentation.fgmc_visible)
	assert(presentation.black_mu_frame == 2)
	assert(presentation.black_overlay_visible())
	assert(str(naruto.last_super.get("face_label", "")) == "鸣人2")
	assert(str(naruto.last_super.get("kind", "")) == "bsd")
	assert(str(naruto.last_super.get("xg", "")) == "XG_bs")
	assert(presentation.face_label == "鸣人2")
	assert(presentation.active_slot == "face_p1")
	assert(presentation.portrait_frame("鸣人2") == 23)
	ichigo.advance_timeline()
	assert(ichigo.current_source_frame() == ichigo_frame)
	var frozen_x := ichigo.position.x
	ichigo.enter_frame({"right": true})
	assert(ichigo.action == "站立")
	assert(ichigo.position.x == frozen_x)
	for _tick in range(30):
		if naruto.current_source_frame() >= 530 and naruto.action == "必杀":
			break
		naruto.advance_timeline()
	assert(naruto.action == "必杀")
	assert(naruto.current_source_frame() == 530)
	naruto.enter_frame({})
	assert(not naruto.zhanting)
	assert(naruto.bs == 0)
	assert(not director.zhanting)
	assert(ichigo.timeline_playing)
	assert(presentation.bgmc_visible)
	assert(presentation.black_mu_frame == 1)
	assert(not presentation.black_overlay_visible())
	assert(presentation.face_label == "")
	naruto.start_action("站立")
	director.reset(naruto, ichigo, [])

	# cbsd@752 uses XG_cbs and 焦点=caster. Source cbsd(pn) → 焦点 p1 when pn==2.
	ichigo.start_action("站立")
	naruto.start_action("超必杀")
	for _tick in range(20):
		if naruto.current_source_frame() >= 752 and naruto.action == "超必杀":
			break
		naruto.advance_timeline()
	assert(naruto.action == "超必杀")
	assert(naruto.current_source_frame() == 752)
	naruto.enter_frame({})
	assert(str(naruto.last_super.get("kind", "")) == "cbsd")
	assert(str(naruto.last_super.get("xg", "")) == "XG_cbs")
	assert(str(naruto.last_super.get("face_label", "")) == "鸣人2")
	assert(director.last_focus == "p1")
	assert(not ichigo.timeline_playing)
	assert(presentation.black_mu_frame == 2)
	var freeze_y := ichigo.position.y
	var freeze_frame := ichigo.current_source_frame()
	for _tick in range(20):
		ichigo.advance_timeline()
		ichigo.enter_frame({"jump": true, "right": true})
		assert(ichigo.action == "站立")
		assert(is_equal_approx(ichigo.position.y, freeze_y))
		assert(ichigo.current_source_frame() == freeze_frame)
	for _tick in range(90):
		if naruto.current_source_frame() >= 829 and naruto.action == "超必杀":
			break
		naruto.advance_timeline()
	assert(naruto.current_source_frame() == 829)
	naruto.enter_frame({})
	assert(str(naruto.last_super.get("kind", "")) == "cbsw")
	assert(director.last_focus == "all")
	assert(not director.zhanting)
	assert(ichigo.timeline_playing)
	assert(presentation.black_mu_frame == 1)
	naruto.start_action("站立")
	director.reset(naruto, ichigo, [])

	# Source beidax() returns on root zhanting before movement and time++.
	# stopMc deliberately does not stop hited clips, so verify callback state
	# separately from the playhead.
	ichigo.start_action("站立")
	ichigo.health = 1000.0
	ichigo.receive_attack(naruto._combat.attacks.cbs2, 1)
	var hurt_freeze_position := ichigo.position
	var hurt_freeze_ticks := ichigo._hurt_motion_ticks
	director.apply({"op": "super_start", "kind": "cbsd"}, naruto, ichigo)
	# Source cbsd calls stopMc(opponent); the receiver is frozen until super reset.
	assert(not ichigo.timeline_playing)
	ichigo.enter_frame({})
	assert(ichigo.position == hurt_freeze_position)
	assert(ichigo._hurt_motion_ticks == hurt_freeze_ticks)
	director.reset(naruto, ichigo, [])
	ichigo.start_action("站立")

	# Defender checkHit() shares gameRunning() across fighter/helper/stage
	# candidates. A helper still playing during zhanting must not deal damage.
	gaara.activate(
		{"x": 200.0, "y": 0.0, "facing": 1, "start_frame": 2},
		naruto
	)
	gaara.play_source_frame(44)
	var helper_bounds := gaara.instance_global_bounds("atm1")
	var defender_bounds := ichigo.instance_global_bounds("bdmn")
	ichigo.position += helper_bounds.get_center() - defender_bounds.get_center()
	director.apply({"op": "super_start", "kind": "cbsd"}, naruto, ichigo, [gaara])
	assert(gaara.timeline_playing) # Source sw is undefined, not strictly false.
	var helper_freeze_health := ichigo.health
	CombatResolverScript.resolve_helpers([gaara], [naruto, ichigo])
	assert(ichigo.health == helper_freeze_health)
	director.reset(naruto, ichigo, [gaara])
	gaara.deactivate()

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

	# fangyu(): cbs1 zl 1 stays blocked, cbs3 zl 14 removes the marker and
	# leaves for 被打 with cbs3up = -3, so beidax() pushes the body down.
	# on_enterframe() is a clip action on the wrapper's PlaceObject of the body
	# mc (frame_1/PlaceObject2_638_1, frame_2/PlaceObject2_1180_1), so it keeps
	# resolving the floor through 被打: its jump == 1 early return only covers
	# `_y < floorY`, and `if(_y > floorY - 10) _y = floorY` pins the defender.
	ichigo.health = 1000.0
	ichigo.position = Vector2(200.0, 0.0)
	ichigo.configure_stage(0.0, [])
	ichigo.start_action("防御2")
	ichigo.enter_frame({"down": true})
	assert(ichigo.guarding)
	ichigo.receive_attack(naruto._combat.attacks.cbs1, 1)
	assert(ichigo.action == "防住")
	# Source DefineSprite_638/frame_727/DoAction.as applies the guard effect on the next receiver frame.
	ichigo.advance_timeline()
	ichigo.run_frame_actions()
	assert(ichigo.last_hit_effect == "XG_fykan")
	assert(ichigo.position.y == 0.0)
	ichigo.start_action("防御2")
	ichigo.enter_frame({"down": true})
	ichigo.receive_attack(naruto._combat.attacks.cbs3, 1)
	assert(ichigo.action == "被打")
	# Source guard-break settlement is also scheduled on the receiver frame.
	ichigo.advance_timeline()
	ichigo.run_frame_actions()
	assert(ichigo.last_hit_effect == "XG_mfdj")
	for _tick in range(30):
		ichigo.advance_timeline()
		ichigo.enter_frame({"down": true})
		ichigo.run_frame_actions()
		assert(ichigo.position.y <= 0.0)

	# 下+I is bishaSuper → 超必杀. 超必杀2@942 self-goto 击飞 with yup/htx;
	# beidax(true) must still land to 击落地 and leave for 站立. Source:
	# DefineSprite_764/frame_942 and frame_1027–1035 / 击落地@1069.
	# doAllAction first leaving goto is defence(); onDefence later-wins 超必杀.
	naruto.sw = false
	naruto.health = 1000.0
	naruto.position = Vector2(200.0, 0.0)
	naruto.configure_stage(0.0, [])
	naruto.start_action("站立")
	naruto.energy = 300.0
	naruto.enter_frame({"down": true, "special": true})
	assert(naruto.action == "防御")
	naruto.advance_timeline()
	naruto.enter_frame({"down": true, "special": true})
	assert(naruto.action == "超必杀")
	var recovered := false
	for _tick in range(400):
		naruto.advance_timeline()
		naruto.enter_frame({})
		naruto.run_frame_actions()
		if naruto.action == "站立" and _tick > 8:
			recovered = true
			break
	assert(recovered)
	assert(is_equal_approx(naruto.position.y, 0.0))
	assert(naruto.current_source_frame() < 1027)
	naruto.enter_frame({"right": true})
	assert(naruto.action == "走")

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
	ichigo.advance_timeline()
	ichigo.run_frame_actions()
	# Source loseHp(v) performs hp -= v without clamping; 8 - 15 = -7 and checkDead sets sw.
	assert(ichigo.health == -7.0)
	assert(ichigo.sw)
	assert(ichigo.action == "击飞")
	assert(ichigo.action != "站立")
	for _tick in range(80):
		ichigo.advance_timeline()
		ichigo.enter_frame({"right": true, "attack": true})
		ichigo.run_frame_actions()
	# Source loseHp remains unclamped across repeated hits: -7 - 15 = -22.
	assert(ichigo.health == -22.0)
	assert(ichigo.sw)
	assert(ichigo.action == "击落地")
	assert(ichigo.action != "站立")
	assert(ichigo.action != "起身")
	assert(ichigo.action != "走")
	var dead_x := ichigo.position.x
	ichigo.enter_frame({"right": true, "left": true, "attack": true, "jump": true})
	assert(ichigo.action == "击落地")
	assert(is_equal_approx(ichigo.position.x, dead_x))

	# Source checkDead: hp <= 0 and modo == 4 does not set sw.
	ichigo.sw = false
	ichigo.health = 8.0
	ichigo.modo = 4
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
	ichigo.advance_timeline()
	ichigo.run_frame_actions()
	# Source loseHp is unclamped in training mode too; checkDead skips sw for modo 4.
	assert(ichigo.health == -7.0)
	assert(not ichigo.sw)
	assert(ichigo.action != "击飞")
	assert(ichigo.beida == 1)
	# Source zdbx: only when modo==4 and beida==0, hp=maxhp and ql=300.
	var zdbx_session := GameSession.new()
	zdbx_session.modo = 4
	zdbx_session.maxhp = 1000.0
	zdbx_session.apply_zdbx([ichigo], true)
	# zdbx is gated by beida==0; this defended receiver remains at its source health.
	assert(ichigo.health == -7.0)
	assert(ichigo.energy != 300.0)
	ichigo.start_action("站立")
	assert(ichigo.beida == 0)
	ichigo.health = 100.0
	ichigo.energy = 10.0
	zdbx_session.apply_zdbx([ichigo], true)
	assert(ichigo.health == 1000.0)
	assert(ichigo.energy == 300.0)
	zdbx_session.modo = 3
	ichigo.health = 100.0
	ichigo.energy = 10.0
	zdbx_session.apply_zdbx([ichigo], true)
	assert(ichigo.health == 100.0)
	assert(ichigo.energy == 10.0)
	ichigo.modo = 1
	ichigo.health = 1000.0
	ichigo.energy = 0.0
	ichigo.start_action("站立")

	naruto.opponent = ichigo
	ichigo.opponent = naruto
	naruto.position = Vector2(200.0, 0.0)
	ichigo.position = Vector2(400.0, 0.0)

	# Source DefineSprite_764/frame_683/DoAction.as: fensheng._x/_y copy the
	# opponent container. New PlaceObject at 683; offset persists to sbsatm.
	naruto.energy = 100.0
	naruto.position = Vector2(150.0, 0.0)
	ichigo.position = Vector2(400.0, 0.0)
	naruto.set_facing(1)
	naruto.start_action("上必杀")
	while naruto.current_source_frame() < 683:
		naruto.advance_timeline()
	assert(naruto.current_source_frame() == 683)
	naruto.enter_frame({})
	naruto.run_frame_actions()
	var clone_origin := naruto.named_instance_origin("fensheng")
	assert(clone_origin != Vector2.INF)
	var clone_local := clone_origin + naruto.instance_local_offset("fensheng")
	assert(is_equal_approx(clone_local.x, ichigo.position.x - naruto.position.x))
	assert(is_equal_approx(clone_local.y, ichigo.position.y - naruto.position.y))
	var clone_world_x := (
		naruto.position.x
		+ float(naruto.facing) * (naruto.wrapper_translation().x + clone_local.x)
	)
	assert(absf(clone_world_x - ichigo.position.x) < absf(clone_world_x - 150.0))
	assert(
		is_equal_approx(
			clone_world_x,
			ichigo.position.x + float(naruto.facing) * naruto.wrapper_translation().x
		)
	)
	while naruto.current_source_frame() < 693:
		naruto.advance_timeline()
		naruto.enter_frame({})
		naruto.run_frame_actions()
	assert(naruto.current_source_frame() == 693)
	clone_origin = naruto.named_instance_origin("fensheng")
	clone_local = clone_origin + naruto.instance_local_offset("fensheng")
	assert(is_equal_approx(clone_local.x, ichigo.position.x - naruto.position.x))
	naruto.start_action("站立")
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
	hit_effect.auto_advance = false
	hit_effect.configure("XG_qdjx", Vector2(200.0, -25.0), 1)
	root.add_child(hit_effect)
	await process_frame
	# Preview plus the frame-1 StartSound player (soundId 219).
	assert(hit_effect.get_child_count() == 2)
	var effect_preview := hit_effect.get_child(0) as TimelinePreview
	assert(effect_preview.current_source_frame() in [1, 2])
	assert(effect_preview.get_child_count() > 0)
	assert(hit_effect.last_sound_ids == [219])
	assert((hit_effect.get_child(1) as AudioStreamPlayer).playing)
	assert(hit_effect.effect_frame == 1)
	assert(not hit_effect.game_paused)
	hit_effect.advance_effect()
	assert(hit_effect.effect_frame == 2)
	assert(hit_effect.game_paused)
	assert("pause_game" in hit_effect.last_ops)
	assert("shine" in hit_effect.last_ops)
	while hit_effect.effect_frame < 15:
		hit_effect.advance_effect()
	assert(not hit_effect.game_paused)
	assert("resume_game" in hit_effect.last_ops)
	hit_effect.auto_advance = true
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

	# Source XG_fykan: frame 1 StartSound 215 with no envelope, frame 11
	# this.unloadMovie(). Blocked 斩 must be seen and heard.
	var guard_effect: HitEffectRuntime = hit_effect_script.new()
	guard_effect.auto_advance = false
	guard_effect.configure("XG_fykan", Vector2(200.0, -25.0), 1)
	root.add_child(guard_effect)
	await process_frame
	var guard_preview := guard_effect.get_child(0) as TimelinePreview
	assert(guard_preview.get_child_count() > 0)
	assert(guard_effect.last_sound_ids == [215])
	var guard_player := guard_effect.get_child(1) as AudioStreamPlayer
	assert(guard_player.playing)
	assert(is_equal_approx(guard_player.volume_db, 0.0))
	while guard_effect.effect_frame < 11:
		guard_effect.advance_effect()
	assert("unload" in guard_effect.last_ops)
	await process_frame
	assert(not is_instance_valid(guard_effect))

	# XG_fyq carries a source SOUNDINFO envelope; the generated sound segment is
	# envelope_baked, so the player uses the baked stream at neutral gain.
	var ring_effect: HitEffectRuntime = hit_effect_script.new()
	ring_effect.auto_advance = false
	ring_effect.configure("XG_fyq", Vector2(200.0, -25.0), 1)
	root.add_child(ring_effect)
	await process_frame
	assert(ring_effect.last_sound_ids == [197])
	var ring_player := ring_effect.get_child(1) as AudioStreamPlayer
	assert(ring_player.playing)
	assert(is_equal_approx(ring_player.volume_db, 0.0))
	ring_effect.queue_free()
	await process_frame

	print("COMBAT_SMOKE_OK")
	quit()
