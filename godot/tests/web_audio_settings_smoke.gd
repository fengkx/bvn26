extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var bridge := root.get_node("WebAudioSettings")
	var bus := AudioServer.get_bus_index("Master")
	var original_db := AudioServer.get_bus_volume_db(bus)
	var original_mute := AudioServer.is_bus_mute(bus)

	bridge.apply_settings(1.0, false)
	assert(is_equal_approx(AudioServer.get_bus_volume_db(bus), 0.0))
	assert(not AudioServer.is_bus_mute(bus))

	bridge.apply_settings(0.25, false)
	assert(is_equal_approx(AudioServer.get_bus_volume_db(bus), linear_to_db(0.25)))
	assert(not AudioServer.is_bus_mute(bus))

	bridge.apply_settings(0.25, true)
	assert(is_equal_approx(AudioServer.get_bus_volume_db(bus), linear_to_db(0.25)))
	assert(AudioServer.is_bus_mute(bus))

	bridge.apply_settings(0.0, false)
	assert(AudioServer.get_bus_volume_db(bus) <= -79.0)
	assert(not AudioServer.is_bus_mute(bus))

	bridge.apply_settings(db_to_linear(original_db), original_mute)
	print("WEB_AUDIO_SETTINGS_SMOKE_OK")
	quit()
