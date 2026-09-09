extends "res://tests/player_body_compile_smoke.gd"


func _initialize() -> void:
	var context := Context.new()
	context.fields["ql"] = 0
	var body = load("res://generated/fighters/minren/player_body/body.gd").new({})
	body.adapter = context
	var callbacks = preload("res://source_body_callbacks.gd").new()
	var metadata: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/fighters/minren/player_body/body.json"))
	callbacks.configure(metadata, body)
	for frame in [1014, 1015, 1016]:
		callbacks.observe(frame, frame)
		callbacks.dispatch(frame)
	assert(context.displacement == Vector2.ZERO and context.fields["time"] == 0)
	callbacks.observe(1017, 1017)
	callbacks.dispatch(1017)
	assert(context.displacement == Vector2(-8, -3) and context.fields["hstm"] == 1)
	# A stopped playhead retains enterFrame, while remove/re-place is fresh.
	callbacks.observe(1017, 1018)
	callbacks.dispatch(1018)
	assert(context.displacement == Vector2(-16, -6))
	callbacks.observe(1014, 1019)
	callbacks.observe(1016, 1019)
	callbacks.dispatch(1019)
	assert(context.displacement == Vector2(-16, -6))
	callbacks.observe(1017, 1020)
	callbacks.dispatch(1020)
	assert(context.displacement == Vector2(-24, -9))
	callbacks.clear()
	callbacks.dispatch(1021)
	assert(context.displacement == Vector2(-24, -9))
	callbacks.configure(metadata, body)
	context.fields["x"] = 0
	context.fields["xscale"] = 100
	context.fields["speed"] = 8
	callbacks.observe(1064, 2000)
	callbacks.dispatch(2000)
	assert(context.fields["x"] == 0)
	for index in 3:
		callbacks.observe(1065 + index, 2001 + index)
		callbacks.dispatch(2001 + index)
	assert(context.fields["x"] == 12)
	callbacks.observe(1068, 2004)
	callbacks.dispatch(2004)
	assert(context.fields["x"] == 12)
	callbacks.observe(1064, 2005)
	context.fields["root_paused"] = true
	callbacks.observe(1065, 2006)
	callbacks.dispatch(2006)
	assert(context.fields["x"] == 12)
	context.fields["root_paused"] = false
	context.fields["xscale"] = -100
	context.fields["speed"] = 3
	callbacks.observe(1066, 2007)
	callbacks.dispatch(2007)
	assert(context.fields["x"] == 10)
	callbacks.clear()
	print("PLAYER_HURT_LIFETIME_SMOKE_OK")
	quit()
