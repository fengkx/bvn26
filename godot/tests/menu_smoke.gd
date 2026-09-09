extends SceneTree

# Source menu timing and existing key/training invariants.
# Paths: scripts/main.json frame_7/DoAction.as, frame_8 showKeyName,
# DefineSprite_620 enterFrame, DefineSprite_600/603 frame_15,
# DefineSprite_835 enterkey, checkDead modo != 4,
# DefineSprite_1991 zdbx / setInterval(zdbx, 1000).


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var session := GameSession.new()
	assert(session.show_key_name(87) == "W")
	assert(session.show_key_name(74) == "J")
	assert(session.show_key_name(38) == "↑")
	assert(session.show_key_name(97) == "Num1")
	assert(session.flash_to_key(87) == KEY_W)
	assert(session.flash_to_key(38) == KEY_UP)
	assert(session.flash_to_key(97) == KEY_KP_1)
	assert(session.key_to_flash(KEY_W) == 87)
	assert(session.key_to_flash(KEY_UP) == 38)
	assert(session.key_to_flash(KEY_KP_1) == 97)
	assert(session.slot_action("j") == "Attack")
	assert(session.slot_action("N2") == "Jump")

	var menu := TitleMenu.new()
	var chosen := []
	menu.confirmed.connect(func(item_id: String) -> void: chosen.append(item_id))
	assert(menu.select == 2 and menu.current_item().id == "vs_com")
	for tick in 62: menu.apply_held({})
	for tick in 10: menu.apply_held({})
	assert(menu.select == 2 and menu.current_item().id == "vs_com")
	menu.apply_held({"confirm": true})
	for tick in 13: menu.apply_held({"confirm": true})
	assert(chosen.is_empty())
	menu.apply_held({"confirm": true})
	assert(chosen == ["vs_com"])

	var keys := KeySettings.new()
	keys.session = session
	assert(keys.row == 1)
	keys.apply_held({"down": true})
	assert(keys.row == 2)
	keys.apply_held({})
	keys.apply_held({"right": true})
	assert(keys.side == 2)
	session.bind_slot("w", 81)
	assert(int(session.codes["w"]) == 81)
	assert(session.show_key_name(81) == "Q")

	var fighter_script = load("res://fighter_runtime.gd")
	var dummy: FighterRuntime = fighter_script.new()
	dummy.fighter_directory = "res://generated/fighters/minren"
	root.add_child(dummy)
	await process_frame
	dummy.modo = 4
	dummy.health = 8.0
	dummy.sw = false
	dummy.start_action("站立")
	dummy.receive_attack(
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
	# Source settlement occurs on the following hurt frame; loseHp has no zero clamp.
	assert(dummy.health == 8.0)
	dummy.run_frame_actions()
	dummy.advance_timeline()
	dummy.run_frame_actions()
	assert(dummy.health == -7.0)
	assert(not dummy.sw)
	assert(dummy.beida == 1)
	assert(dummy.action != "击飞")
	dummy.enter_frame({"right": true})
	assert(dummy.action in ["被打", "走", "站立"])

	menu.free()
	keys.free()
	dummy.queue_free()
	await process_frame
	print("MENU_SMOKE_OK")
	quit()
