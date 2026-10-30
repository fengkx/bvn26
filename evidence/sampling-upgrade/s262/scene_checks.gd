# Appended only to a temporary copy of the existing case runner.
# Callback replay is isolated: the production HUD is not seeded with native state.
var s262_contract: Dictionary
var s262_rows: Array = []
var s262_next_firing := 0
var s262_adapter: S262CallbackAdapter
var s262_callback: RefCounted

class S262CallbackAdapter extends RefCounted:
	var values: Dictionary
	var digits: Dictionary
	func read(key: String) -> Variant:
		assert(values.has(key), "Unobserved callback input: " + key)
		return values[key]
	func write(key: String, value: Variant) -> void:
		values[key] = value
	func set_playing(_target: String, _value: bool) -> void:
		assert(false, "Timeout is outside this bounded replay")
	func goto_clip(target: String, frame: Variant, playing: bool) -> void:
		assert(not playing)
		digits[target] = int(frame)

func _s262_observe(tick: int) -> void:
	if s262_contract.is_empty():
		s262_contract = JSON.parse_string(FileAccess.get_file_as_string(OS.get_environment("S262_CONTRACT")))
		var registration: Dictionary = s262_contract.tape.registration[1]
		s262_adapter = S262CallbackAdapter.new()
		s262_adapter.values = {"_root.gametime": int(registration.gametime)}
		s262_adapter.digits = {"十": int(registration.tens), "个": int(registration.ones)}
		s262_callback = load("res://generated/main/timeout/timer.gd").new()
		s262_callback.adapter = s262_adapter
	var expected: Dictionary = s262_contract.tape.snapshots[tick].before
	while s262_next_firing < int(expected.firing):
		var firing: Dictionary = s262_contract.tape.firings[s262_next_firing]
		var before: Dictionary = firing.before
		s262_adapter.values["_root.zhanting"] = before.paused == "true"
		s262_adapter.values["_root.game.p1.mc.sw"] = before.p1_sw == "true"
		s262_adapter.values["_root.game.p2.mc.sw"] = before.p2_sw == "true"
		s262_adapter.values["_root.modo"] = int(before.modo)
		assert(int(firing.after.gametime) > 0)
		s262_callback.time()
		assert(int(s262_adapter.values["_root.gametime"]) == int(firing.after.gametime))
		assert(s262_adapter.digits == {"十": int(firing.after.tens), "个": int(firing.after.ones)})
		s262_next_firing += 1
	assert(int(s262_adapter.values["_root.gametime"]) == int(expected.gametime))
	var nodes: Dictionary = s262_contract.snapshots[tick].nodes
	var native_state := {
		"tens": int(expected.tens), "ones": int(expected.ones),
		"hud_frame": int(nodes.hud.frame),
		"camera_x": float(nodes.camera.x), "camera_y": float(nodes.camera.y),
		"camera_scale": float(nodes.camera.xscale),
		"root_x": float(nodes.root.x), "root_y": float(nodes.root.y)}
	var actual := {
		"tens": int(game.countdown.digit_frames["十"]), "ones": int(game.countdown.digit_frames["个"]),
		"hud_frame": game.battle_intro.hud_frame,
		"camera_x": game.game_world.game_x, "camera_y": game.game_world.game_y,
		"camera_scale": game.game_world._game_scale_percent,
		"root_x": game.position.x, "root_y": game.position.y}
	for index in 2:
		var side := "p%d" % (index + 1)
		var matches: Array = nodes.values().filter(func(node: Dictionary) -> bool:
			return str(node.role).ends_with("/" + side + "xt/bar2"))
		assert(matches.size() == 1, "HUD bar must bind uniquely")
		native_state[side + "_trail"] = float(matches[0].xscale)
		actual[side + "_trail"] = game.health_hud.trail[index]
		matches = nodes.values().filter(func(node: Dictionary) -> bool:
			return str(node.role).ends_with("/" + side + "xt/win"))
		assert(matches.size() == 1, "HUD win child must bind uniquely")
		native_state[side + "_win"] = int(matches[0].frame)
		actual[side + "_win"] = int(game.health_hud.win_frames[index])
	var differences := []
	for key in native_state:
		if actual[key] != native_state[key]:
			differences.append({"field": key, "native": native_state[key], "godot": actual[key]})
	s262_rows.append({"tick": tick, "native_display": expected.display,
		"replayed_firings": s262_next_firing, "native": native_state, "godot": actual,
		"differences": differences,
		"hud_trail": game.health_hud.trail.duplicate(),
		"hud_low_frame": game.health_hud.low_frame.duplicate(),
		"hud_win_frames": Array(game.health_hud.win_frames)})

func _s262_finish() -> void:
	assert(s262_rows.size() == 61)
	assert(s262_next_firing == int(s262_contract.tape.firing_count))
	var report := {"production_admitted": false, "native_parity_proven": false,
		"common_visual_phase_proved": false, "imaging_allowed": false, "images_written": 0,
		"callback_outputs_verified": s262_next_firing, "rows": s262_rows,
		"state_comparisons_passed": s262_rows.all(func(row: Dictionary) -> bool: return row.differences.is_empty()),
		"unproved_contract": s262_contract.unproved,
		"rejection": "No proved registration-to-intro join or allocation/child-clock history; native state was not assigned to the scene."}
	FileAccess.open(OS.get_environment("S262_SCENE_OUTPUT"), FileAccess.WRITE).store_string(JSON.stringify(report, "\t", true, true))
	print("S262_PREIMAGE_REJECTED callbacks=", s262_next_firing, " snapshots=", s262_rows.size())
	quit(1)
