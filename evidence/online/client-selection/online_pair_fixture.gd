extends Node

const SURFACE_SCENE := preload("res://render_surface.tscn")

var _surface: RenderSurface
var _lobby: OnlineLobby
var _role := ""
var _poll_elapsed := 0.0
var _create_started := false
var _join_started := false
var _connect_started := false
var _ready_started := false
var _leave_started := false
var _saw_prepare_phase := false
var _saw_active_phase := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_role = str(JavaScriptBridge.eval("new URLSearchParams(location.search).get('peer') || ''"))
	_surface = SURFACE_SCENE.instantiate() as RenderSurface
	_surface.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(_surface)
	await get_tree().process_frame
	await get_tree().process_frame
	_lobby = _surface.online_lobby
	_lobby._open_home()
	_lobby._endpoint.text = "http://127.0.0.1:8787"
	_lobby._nickname.text = "Local Host" if _role == "host" else "Local Guest"
	if _role == "host":
		_create_started = true
		_create_room()
	else:
		_publish_status()


func _process(delta: float) -> void:
	if _lobby == null:
		return
	_poll_elapsed += delta
	if _poll_elapsed < 0.15:
		return
	_poll_elapsed = 0.0
	if _role == "guest" and not _join_started and _lobby._room_id.is_empty():
		var invitation := str(JavaScriptBridge.eval("window.__bvnOnlinePairInviteCode || ''"))
		if not invitation.is_empty():
			_join_started = true
			_lobby._room_code.text = invitation
			_join_room()
	if _room_admitted() and not _lobby._lan_candidate_opt_in.button_pressed:
		_lobby._lan_candidate_opt_in.button_pressed = true
	if _can_connect() and not _connect_started and _browser_flag("__bvnOnlinePairConnect"):
		_connect_started = true
		_connect_room()
	if _can_ready() and not _ready_started and _browser_flag("__bvnOnlinePairReady"):
		_ready_started = true
		_ready_player()
	if not _lobby._room_id.is_empty() and not _leave_started and _browser_flag("__bvnOnlinePairLeave"):
		if _lobby._startup_busy and _lobby._startup_cancel_button != null \
			and _lobby._startup_cancel_button.is_visible_in_tree() \
			and not _lobby._startup_cancel_button.disabled:
			_leave_started = true
			_cancel_startup_and_leave()
		elif not _lobby._busy:
			_leave_started = true
			_leave_room()
	_publish_status()


func _create_room() -> void:
	await _lobby._on_create_pressed()
	_watch_room_state()
	_publish_status()
	if not _lobby._invite_code.is_empty():
		JavaScriptBridge.eval("window.__bvnOnlinePairInviteCode=" + JSON.stringify(_lobby._invite_code))


func _join_room() -> void:
	await _lobby._on_join_pressed()
	_watch_room_state()
	_publish_status()


func _connect_room() -> void:
	await _lobby._on_connect_selection_pressed()
	_publish_status()


func _ready_player() -> void:
	if _lobby._selection_active or _lobby._busy:
		_ready_started = false
		return
	await _lobby._on_ready_pressed()
	_publish_status()


func _leave_room() -> void:
	await _lobby._on_leave_room_pressed()
	_publish_status()


func _cancel_startup_and_leave() -> void:
	await _lobby._on_cancel_start_pressed()
	if not _lobby._room_id.is_empty() and not _lobby._busy:
		await _lobby._on_leave_room_pressed()
	_publish_status()


func _watch_room_state() -> void:
	if _lobby.room_client != null and not _lobby.room_client.state_changed.is_connected(_on_service_state_changed):
		_lobby.room_client.state_changed.connect(_on_service_state_changed)
	_on_service_state_changed(_lobby._room_state)


func _on_service_state_changed(state: Dictionary) -> void:
	match str(state.get("phase", "")):
		"preparing":
			_saw_prepare_phase = true
		"active":
			_saw_active_phase = true


func _room_admitted() -> bool:
	if _lobby == null or _lobby._room_id.is_empty():
		return false
	var members: Array = _lobby._room_state.get("members", [])
	return members.size() == 2 and members.all(func(member: Variant) -> bool: return member is Dictionary)


func _committed_choices() -> bool:
	if not _room_admitted() or _lobby._selection_active or _lobby._selection_commit_busy:
		return false
	var members: Array = _lobby._room_state.get("members", [])
	for member in members:
		var choice: Variant = member.get("choice") if member is Dictionary else null
		if not choice is Dictionary or str(choice.get("fighter", "")).is_empty() or str(choice.get("helper", "")).is_empty():
			return false
	return true


func _can_connect() -> bool:
	return _room_admitted() and not _lobby._busy and not _lobby._room_connection_starting \
		and _lobby._connect_selection_button != null \
		and _lobby._connect_selection_button.is_visible_in_tree() \
		and not _lobby._connect_selection_button.disabled


func _can_ready() -> bool:
	var primary_button: Button = _lobby._connect_selection_button
	return _committed_choices() and not _lobby._busy and _lobby._room_primary_action == "ready" \
		and primary_button != null and primary_button.is_visible_in_tree() and not primary_button.disabled


func _browser_flag(name: String) -> bool:
	return bool(JavaScriptBridge.eval("window.%s === true" % name))


func _publish_status() -> void:
	if _lobby == null:
		return
	var members: Array = _lobby._room_state.get("members", [])
	var map_adapter := _map_adapter()
	var room_rules: Dictionary = _lobby._room_state.get("rules", {})
	var desired_rules: Dictionary = _lobby._selected_rules()
	var choices: Array = []
	var ready: Array = []
	for member in members:
		var row: Dictionary = member if member is Dictionary else {}
		choices.append(row.get("choice", {}))
		ready.append(bool(row.get("ready", false)))
	var status := {
		"role": _role,
		"slot": _lobby._slot,
		"admitted": _room_admitted(),
		"hasRoom": not _lobby._room_id.is_empty(),
		"memberCount": members.size(),
		"phase": str(_lobby._room_state.get("phase", "")),
		"sawPreparePhase": _saw_prepare_phase,
		"sawActivePhase": _saw_active_phase,
		"revision": int(_lobby._room_state.get("revision", -1)),
		"setupRevision": int(_lobby._room_state.get("setupRevision", -1)),
		"serviceStage": str(_lobby._room_state.get("stage", "")),
		"primaryAction": _lobby._room_primary_action,
		"advancedCollapsed": _lobby._advanced_toggle == null or not _lobby._advanced_toggle.button_pressed,
		"serviceRules": room_rules.duplicate(true),
		"serviceRuleTypes": {
			"time": typeof(room_rules.get("time")),
			"life": typeof(room_rules.get("life")),
		},
		"desiredRules": desired_rules.duplicate(true),
		"desiredRuleTypes": {
			"time": typeof(desired_rules.get("time")),
			"life": typeof(desired_rules.get("life")),
		},
		"mapSelectionVisible": _lobby._map_active and map_adapter != null and map_adapter.is_visible_in_tree(),
		"mapSelectionEnabled": map_adapter != null and map_adapter.enabled,
		"mapHostAuthority": map_adapter != null and map_adapter.host_authority,
		"mapSelectionStage": map_adapter.selected_stage() if map_adapter != null else "",
		"mapSourceFrame": map_adapter.source_frame if map_adapter != null else -1,
		"mapStopFrame": int(map_adapter.spec.get("stop_frame", -1)) if map_adapter != null else -1,
		"mapHandshakeComplete": _lobby._map_handshake_complete,
		"startupCancelVisible": _lobby._startup_cancel_button != null and _lobby._startup_cancel_button.is_visible_in_tree(),
		"startupCancelEnabled": _lobby._startup_cancel_button != null and not _lobby._startup_cancel_button.disabled,
		"connectionStarting": _lobby._room_connection_starting,
		"connectionReady": _lobby._room_connection_ready,
		"connectionState": str(_lobby._room_connection.get("_connection_state")) if _lobby._room_connection != null else "none",
		"connectionIssue": str(_lobby._room_connection.get("_signal_error")) if _lobby._room_connection != null else "",
		"lanOptIn": _lobby._lan_candidate_opt_in.button_pressed,
		"profileDraftDirty": _lobby._profile_draft_dirty,
		"connectAttempted": _connect_started,
		"connectRequested": _browser_flag("__bvnOnlinePairConnect"),
		"canConnect": _can_connect(),
		"selectionActive": _lobby._selection_active,
		"selectionPhase": int(_lobby._selection_adapter.phase) if _lobby._selection_adapter != null else -1,
		"localChoice": _lobby._selection_adapter._local_choice_resource_ids() if _lobby._selection_adapter != null else {},
		"committedChoices": choices,
		"committed": _committed_choices(),
		"canReady": _can_ready(),
		"ready": ready,
		"busy": _lobby._busy,
		"inviteReady": not _lobby._invite_code.is_empty() if _role == "host" else false,
		"errorCode": str(_lobby.room_client.get_last_http_diagnostic().get("error", "")) if _lobby.room_client != null and _lobby.room_client.has_method("get_last_http_diagnostic") else "",
		"statusText": _lobby._status.text,
	}
	JavaScriptBridge.eval("window.__bvnOnlinePairStatus=" + JSON.stringify(status))
	if _role == "host" and not _lobby._invite_code.is_empty():
		JavaScriptBridge.eval("window.__bvnOnlinePairInviteCode=" + JSON.stringify(_lobby._invite_code))


func _map_adapter() -> OnlineMapSelectionAdapter:
	if _lobby == null or _lobby._map_adapter == null or not is_instance_valid(_lobby._map_adapter):
		return null
	return _lobby._map_adapter as OnlineMapSelectionAdapter
