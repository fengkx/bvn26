extends SceneTree


class Context extends RefCounted:
	var fields := {"hp": 1000, "sw": false, "ql": 100, "opponent_action": 0,
		"useAI": false, "goran": 0, "dashQL": 10, "动作": 0,
		"opponent_sw": false, "opponent_x": 100, "x": 0,
		"hitBan": false, "touch": true, "root_paused": false,
		"hitNear": false, "htx": 8, "yup": 3, "hstm": 0,
		"hurtSkling": false, "time": 0, "tdtime": 21}
	var keys: Dictionary = {}
	var displacement := Vector2.ZERO
	var colors_applied := 0

	func read_field(key: String) -> Variant:
		return fields.get(key)

	func write_field(key: String, value: Variant) -> void:
		fields[key] = value

	func source_key(key: String) -> bool:
		return keys.get(key, false)

	func move_body(other: bool, axis: String, amount: Variant) -> void:
		assert(not other)
		if axis == "moveX": displacement.x += float(amount)
		else: displacement.y += float(amount)

	func body_service(name: String) -> Variant:
		assert(name == "applyColors")
		colors_applied += 1
		return null


func _initialize() -> void:
	var context := Context.new()
	var body = load("res://generated/fighters/minren/player_body/body.gd").new({})
	body.adapter = context
	assert(body.hurtSkill() == false)
	context.keys["换"] = true
	context.fields["goran"] = 499
	assert(body.hurtSkill() == true)
	context.fields["opponent_action"] = 3
	assert(body.hurtSkill() == false)
	context.fields["opponent_action"] = 0
	context.keys = {"冲": true, "上": true}
	assert(body.dash() == true)
	assert(context.fields["dashX"] == 0 and context.fields["dashY"] == -14)
	context.keys.clear()
	context.fields["ql"] = 0
	body.beidax()
	assert(context.displacement == Vector2(-8, -3))
	assert(context.fields["hstm"] == 1 and context.fields["time"] == 1)
	context.fields["root_paused"] = true
	body.beidax()
	assert(context.colors_applied == 2)
	assert(context.displacement == Vector2(-8, -3) and context.fields["time"] == 1)
	print("PLAYER_BODY_COMPILE_SMOKE_OK")
	quit()
