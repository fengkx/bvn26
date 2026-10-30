# Analysis-only replay of the recorded callback through the existing compiled source.
extends SceneTree

class TapeAdapter extends RefCounted:
	var values: Dictionary
	var digits: Dictionary
	func read(key: String) -> Variant:
		assert(values.has(key), "Unobserved callback input: " + key)
		return values[key]
	func write(key: String, value: Variant) -> void:
		values[key] = value
	func set_playing(_target: String, _value: bool) -> void:
		assert(false, "Timeout side effect is outside this tape replay")
	func goto_clip(target: String, frame: Variant, playing: bool) -> void:
		assert(not playing)
		digits[target] = int(frame)

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 1)
	var result: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	var tape: Dictionary = result.tape
	var adapter := TapeAdapter.new()
	var registered: Dictionary = tape.registration[1]
	adapter.values = {"_root.gametime": int(registered.gametime)}
	adapter.digits = {"十": int(registered.tens), "个": int(registered.ones)}
	var callback = load("res://generated/main/timeout/timer.gd").new()
	callback.adapter = adapter
	for firing in tape.firings:
		var before: Dictionary = firing.before
		var after: Dictionary = firing.after
		assert(int(adapter.values["_root.gametime"]) == int(before.gametime))
		adapter.values["_root.zhanting"] = before.paused == "true"
		adapter.values["_root.game.p1.mc.sw"] = before.p1_sw == "true"
		adapter.values["_root.game.p2.mc.sw"] = before.p2_sw == "true"
		adapter.values["_root.modo"] = int(before.modo)
		# Do not invent the timeover.played input if this capture reaches timeout.
		assert(int(after.gametime) > 0, "Timeout requires additional observed inputs")
		callback.time()
		assert(int(adapter.values["_root.gametime"]) == int(after.gametime))
		assert(adapter.digits == {"十": int(after.tens), "个": int(after.ones)})
	print("S258_RECORDED_CALLBACK_REPLAY_OK firings=", tape.firing_count)
	quit()
