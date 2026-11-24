extends SceneTree


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var menu := TitleMenu.new()
	root.add_child(menu)
	await process_frame
	for child in menu.get_children():
		if child is AudioStreamPlayer:
			menu.remove_child(child)
			child.free()
	menu._sounds.clear()
	menu.source_frame = 63
	menu._wheel_born = true
	menu.controller.reset()
	menu.controller.select = 2
	menu._refresh()
	assert(menu.current_item().id == "vs_com")
	for expected in [3, 4, 5, 6, 1]:
		_move(menu, "down")
		assert(menu.select == expected, "Down navigation skipped menu slot: %d" % expected)
		if expected == 6:
			assert(menu.current_item().id == "online")
			menu._refresh()
			var sprite: Sprite2D = menu._buttons[menu.ONLINE_SLOT]
			assert(sprite.visible and sprite.texture == menu.ONLINE_ART)
			assert(menu._online_entry.position == sprite.position)
			assert(menu._online_entry.size.is_equal_approx(sprite.texture.get_size()))
	_move(menu, "up")
	assert(menu.select == 6 and menu.current_item().id == "online")
	var confirmed_ids: Array[String] = []
	menu.confirmed.connect(func(item_id: String) -> void: confirmed_ids.append(item_id))
	menu._online_entry.pressed.emit()
	assert(confirmed_ids.is_empty() and menu.pending_item.id == "online")
	for _frame in 14:
		menu.apply_held({})
		if menu.button_frame in [3, 5]:
			var tint: Color = menu._buttons[menu.ONLINE_SLOT].material.get_shader_parameter("cx_add")
			assert(tint == (Color(1, 1, 1, 0) if menu.button_frame == 3 else menu._online_tint))
	assert(confirmed_ids == ["online"], "Mouse confirmation skipped the source menu animation")
	menu.reset()
	menu.source_frame = 63
	menu._wheel_born = true
	menu.controller.select = 2
	menu._refresh()
	for expected in [3, 4, 5, 6]:
		_move(menu, "down")
		assert(menu.select == expected)
	menu.apply_held({"confirm": true})
	for _frame in 14:
		menu.apply_held({})
	assert(confirmed_ids == ["online", "online"], "Keyboard confirmation did not emit the online menu item")
	menu.pending_item = menu.current_item().duplicate(true)
	menu.controller.anj = 1
	menu.reset()
	assert(menu.pending_item.is_empty() and menu.controller.anj == 0)
	print("TITLE_MENU_ONLINE_SMOKE_OK cycle_down=true cycle_up=true signal_entry=true keyboard_confirmation=true reset=true")
	menu.queue_free()
	await process_frame
	quit(0)


func _move(menu: TitleMenu, direction: String) -> void:
	menu._navigation_direction = -1 if direction == "up" else 1
	menu.controller.tick({direction: true})
	menu._skip_unavailable()
	for _frame in 80:
		if menu.controller.an == 0 and absf(float(menu.controller.positions[menu.select])) < 6.0:
			return
		menu.controller.tick({})
		menu._skip_unavailable()
	assert(false, "Menu navigation animation did not settle")
