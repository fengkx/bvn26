extends Node

const MASTER_BUS := "Master"
const SILENCE_DB := -80.0

var _master_bus_index := -1
var _shell_callback


func _ready() -> void:
	_master_bus_index = AudioServer.get_bus_index(MASTER_BUS)
	if _master_bus_index < 0:
		push_error("Web audio settings could not find the Master bus")
		return
	if not OS.has_feature("web"):
		return
	_shell_callback = JavaScriptBridge.create_callback(_on_shell_settings_changed)
	var window = JavaScriptBridge.get_interface("window")
	window.bvnGodotAudioSettingsChanged = _shell_callback
	window.bvnRegisterAudioSettings(_shell_callback)


func _exit_tree() -> void:
	if not OS.has_feature("web") or _shell_callback == null:
		return
	var window = JavaScriptBridge.get_interface("window")
	window.bvnUnregisterAudioSettings(_shell_callback)
	window.bvnGodotAudioSettingsChanged = null
	_shell_callback = null


func _on_shell_settings_changed(args: Array) -> void:
	if args.size() < 2 or typeof(args[0]) not in [TYPE_FLOAT, TYPE_INT] or typeof(args[1]) != TYPE_BOOL:
		push_warning("Ignored malformed Web audio settings callback")
		return
	apply_settings(float(args[0]), bool(args[1]))


func apply_settings(linear_volume: float, muted: bool) -> void:
	if _master_bus_index < 0 or not is_finite(linear_volume):
		return
	var safe_volume := clampf(linear_volume, 0.0, 1.0)
	var volume_db := SILENCE_DB if safe_volume == 0.0 else linear_to_db(safe_volume)
	AudioServer.set_bus_volume_db(_master_bus_index, volume_db)
	AudioServer.set_bus_mute(_master_bus_index, muted)
	_publish_applied_state()


func _publish_applied_state() -> void:
	if not OS.has_feature("web"):
		return
	var window = JavaScriptBridge.get_interface("window")
	window.bvnAudioSettingsApplied(
		AudioServer.get_bus_volume_db(_master_bus_index),
		AudioServer.is_bus_mute(_master_bus_index)
	)
