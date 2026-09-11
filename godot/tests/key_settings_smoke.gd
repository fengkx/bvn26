extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func press(code: Key, down: bool) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.keycode = code
	event.pressed = down
	Input.parse_input_event(event)
	Input.flush_buffered_events()

func _run() -> void:
	var keys := KeySettings.new()
	keys.session = GameSession.new()
	root.add_child(keys)
	assert(keys.row == 0 and keys._current_slot() == "")
	for label in keys._p1_rows + keys._p2_rows:
		assert(not label.text.begins_with(">"))
	keys.apply_held({"confirm": true})
	assert(not keys.capturing and not keys.waiting_release)
	keys.apply_held({})
	# The reported configuration maps both Up and Right to D.
	keys.session.bind_slot("w", 68)
	press(KEY_RIGHT, true)
	keys.apply_held(keys.navigation_held())
	assert(keys.side == 2 and keys.row == 1)
	press(KEY_RIGHT, false)
	keys.apply_held(keys.navigation_held())
	assert(keys._p2_rows[0].text == "> Up  Up")
	assert(keys._hint.text.contains("Arrow keys"))
	press(KEY_ENTER, true)
	keys.apply_held(keys.navigation_held())
	assert(keys.waiting_release and not keys.capturing)
	press(KEY_ENTER, false)
	keys.apply_held(keys.navigation_held())
	assert(keys.capturing)
	press(KEY_R, true)
	assert(not keys.capturing)
	assert(keys.session.codes["上箭"] == 82)
	assert(keys.session.codes["w"] == 68)
	press(KEY_R, false)
	keys.apply_held(keys.navigation_held())
	press(KEY_LEFT, true)
	keys.apply_held(keys.navigation_held())
	assert(keys.side == 1)
	press(KEY_LEFT, false)
	keys.reset()
	assert(keys.row == 0 and not keys.capturing)
	for label in keys._p1_rows + keys._p2_rows:
		assert(not label.text.begins_with(">"))
	keys.queue_free()
	await process_frame
	print("KEY_SETTINGS_SMOKE_OK")
	quit()
