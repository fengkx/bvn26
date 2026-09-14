class_name DiagnosticRuntime
extends Node

signal event_recorded(event: Dictionary)
signal visibility_changed(visible: bool)

const SCHEMA_VERSION := 2
const MAX_SNAPSHOT_BYTES := 16384

var sequence: int = 0
var match_id: String = ""
var build_id: String = ""
var resource_version: String = ""
var page_visible: bool = true
var _snapshot: Dictionary = {}
var _web_callback: JavaScriptObject
var _web_window: JavaScriptObject
var snapshot_provider: Callable


func _ready() -> void:
	_read_embedded_build_metadata()
	if not OS.has_feature("web"):
		return
	_web_window = JavaScriptBridge.get_interface("window")
	if _web_window == null:
		return
	_web_callback = JavaScriptBridge.create_callback(_on_shell_request)
	_web_window.bvnDiagnosticsRegister(_web_callback)
	push_event("runtime_ready", {"schemaVersion": SCHEMA_VERSION,
		"godot": Engine.get_version_info().get("string", "unknown"),
		"buildID": build_id, "resourceVersion": resource_version})


func _exit_tree() -> void:
	if OS.has_feature("web") and _web_window != null and _web_callback != null:
		_web_window.bvnDiagnosticsUnregister(_web_callback)


func begin_match(snapshot: Dictionary) -> void:
	match_id = "%d-%d" % [Time.get_ticks_usec(), get_instance_id()]
	_snapshot = snapshot.duplicate(true)
	_snapshot["matchId"] = match_id
	_snapshot["schemaVersion"] = SCHEMA_VERSION
	_snapshot["buildID"] = build_id
	_snapshot["resourceVersion"] = resource_version
	_snapshot = _bounded_snapshot(_snapshot)
	push_event("match_started", {"match": _snapshot})
	_set_shell_snapshot()


func end_match(reason: String) -> void:
	if match_id.is_empty():
		return
	push_event("match_ended", {"matchId": match_id, "reason": reason})
	match_id = ""


func push_event(event_type: String, payload: Dictionary = {}, fight_tick: int = -1) -> Dictionary:
	if match_id.is_empty() and event_type != "runtime_ready":
		return {}
	sequence += 1
	var event := {
		"seq": sequence,
		"type": event_type,
		"monoMs": Time.get_ticks_msec(),
		"payload": payload,
		"buildID": build_id,
	}
	if not match_id.is_empty():
		event["matchId"] = match_id
	if fight_tick >= 0:
		event["fightTick"] = fight_tick
	event_recorded.emit(event.duplicate(true))
	if OS.has_feature("web") and _web_window != null:
		_web_window.bvnDiagnosticsPush(JSON.stringify(event))
	return event


func set_snapshot(snapshot: Dictionary) -> void:
	if match_id.is_empty():
		return
	_snapshot = snapshot.duplicate(true)
	_snapshot["matchId"] = match_id
	_snapshot["schemaVersion"] = SCHEMA_VERSION
	_snapshot["buildID"] = build_id
	_snapshot["resourceVersion"] = resource_version
	_snapshot = _bounded_snapshot(_snapshot)
	_set_shell_snapshot()


func pause_snapshot(reason: String, snapshot: Dictionary) -> void:
	set_snapshot(snapshot)
	push_event("pause_state", {"reason": reason, "pause": _snapshot.get("pause", {})})


func freeze_diagnostic(reason: String, detail: Dictionary, snapshot: Dictionary) -> void:
	# This freezes only the diagnostic record. It never pauses the match.
	set_snapshot(snapshot)
	push_event("diagnostic_exception", {"reason": reason, "detail": detail,
		"snapshot": _snapshot})


func _on_shell_request(args: Array) -> void:
	if args.is_empty():
		return
	if str(args[0]) == "visibility" and args.size() >= 2:
		var value: Variant = args[1]
		page_visible = value == true or str(value) == "visible"
		visibility_changed.emit(page_visible)
		push_event("page_visibility", {"visible": page_visible})
		return
	if args.size() < 2 or str(args[0]) != "snapshot":
		return
	var request_id := str(args[1])
	var current: Dictionary = snapshot_provider.call() if snapshot_provider.is_valid() else _snapshot
	var snapshot := current.duplicate(true)
	snapshot["matchId"] = match_id
	snapshot["schemaVersion"] = SCHEMA_VERSION
	snapshot = _bounded_snapshot(snapshot)
	var response := {"requestId": request_id, "buildID": build_id,
		"resourceVersion": resource_version, "match": snapshot}
	_web_window.bvnDiagnosticsSetSnapshot(JSON.stringify(response))


func _set_shell_snapshot() -> void:
	if OS.has_feature("web") and _web_window != null:
		_web_window.bvnDiagnosticsSetSnapshot(JSON.stringify({
			"buildID": build_id,
			"resourceVersion": resource_version,
			"match": _snapshot,
		}))


func _bounded_snapshot(snapshot: Dictionary) -> Dictionary:
	var encoded := JSON.stringify(snapshot)
	if encoded.to_utf8_buffer().size() <= MAX_SNAPSHOT_BYTES:
		return snapshot
	return {"schemaVersion": SCHEMA_VERSION, "matchId": match_id,
		"buildID": build_id, "resourceVersion": resource_version,
		"truncated": true, "originalBytes": encoded.to_utf8_buffer().size()}


func _read_embedded_build_metadata() -> void:
	const path := "res://generated/build_metadata.json"
	if not FileAccess.file_exists(path):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not parsed is Dictionary:
		push_error("Invalid embedded build metadata: " + path)
		return
	build_id = str(parsed.get("buildID", ""))
	resource_version = str(parsed.get("resourceVersion", ""))
