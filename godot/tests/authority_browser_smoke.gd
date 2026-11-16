extends Node

var lobby: OnlineLobby
var ready_sent := false
var setup_started := false
var start_sent := false
var finished := false
var local_ticks := 0
var phase := "boot"
var remote_right_seen := false

func _ready() -> void:
	if bool(JavaScriptBridge.eval("new URLSearchParams(location.search).has('offline')")):
		add_child(preload("res://tests/authority_browser_projection.gd").new())
		return
	var surface: RenderSurface = load("res://render_surface.tscn").instantiate()
	add_child(surface)
	lobby = surface.online_lobby
	lobby._open_home()
	lobby._endpoint.text = "http://127.0.0.1:8787"
	var invite := str(JavaScriptBridge.eval("new URLSearchParams(location.search).get('invite') || ''"))
	lobby._nickname.text = "Authority browser smoke"
	if invite.is_empty():
		await lobby._on_create_pressed()
		if lobby._room_id.is_empty(): return _fail("create:" + lobby._status.text)
		assert(lobby._authority_mode())
		await lobby._submit_operation({"type": "configure_network", "revision": int(lobby._room_state.setupRevision),
			"profile": {"id": "chrome-exp-d2-p6-lan", "inputDelay": 2, "predictionWindow": 6}})
		_publish({"phase": "invite", "invite": lobby._invite_code})
	else:
		lobby._room_code.text = invite
		await lobby._on_join_pressed()
		if lobby._room_id.is_empty(): return _fail("join:" + lobby._status.text)
	phase = "lobby"

func _physics_process(_delta: float) -> void:
	if lobby == null or finished or phase == "boot": return
	if not setup_started and phase == "lobby":
		setup_started = true
		_prepare_room.call_deferred()
	if lobby._slot == 0 and not start_sent and lobby._can_prepare_current_room() and not lobby._busy:
		start_sent = true
		lobby._on_start_pressed()
	if not ready_sent and lobby._can_ready_current_room() and not lobby._busy:
		ready_sent = true
		lobby._on_ready_pressed()
	if not lobby._match_started:
		if not lobby._starting_epoch.is_empty(): phase = "starting"
		return
	phase = "playing"
	var match_state: RefCounted = lobby.coordinator
	if match_state == null: return
	local_ticks += 1
	if match_state._is_host() and match_state._inputs.held.right: remote_right_seen = true
	if local_ticks < 90 and match_state.intro_skippable(): match_state.request_intro_skip()
	if local_ticks % 30 == 0:
		_publish({"phase": phase, "localTicks": local_ticks, "authority": match_state.authority_slot,
			"slot": lobby._slot, "simTicks": lobby.game_root.physics_tick,
			"stateSerial": match_state._received_serial, "running": match_state.running,
			"error": match_state.error, "paused": match_state.paused, "positions": _positions(match_state), "rightKey": lobby.game_root.session.codes.d})
	if local_ticks == 480:
		finished = true
		_publish({"phase": "complete", "authority": match_state.authority_slot, "slot": lobby._slot,
			"simTicks": lobby.game_root.physics_tick, "receivedStates": match_state._received_serial,
			"running": match_state.running, "error": match_state.error, "notAPass": true,
			"positions": _positions(match_state), "remoteRightSeen": remote_right_seen})
		print("AUTHORITY_BROWSER_SMOKE_OK " + JSON.stringify(match_state.performance_report()))

func _process(_delta: float) -> void:
	if lobby != null and not finished:
		JavaScriptBridge.eval("globalThis.authorityStatus = " + JSON.stringify({"phase": phase, "status": lobby._status.text, "matchStatus": lobby._match_status.text}))

func _publish(value: Dictionary) -> void:
	JavaScriptBridge.eval("globalThis.authoritySmoke = " + JSON.stringify(value))

func _fail(reason: String) -> void:
	finished = true
	_publish({"phase": "failed", "reason": reason})
	push_error(reason)

func _positions(match_state: RefCounted) -> Array:
	var result := [null, null]
	for record in match_state._latest_display.get("owners", []):
		if record.kind != "timeline": continue
		var resource: String = match_state._projector.resources[record.state.resource]
		if resource == "res://generated/fighters/sasuke": result[0] = record.transform[4]
		if resource == "res://generated/fighters/rifagu": result[1] = record.transform[4]
	return result

func _prepare_room() -> void:
	lobby._open_lineup()
	var adapter = lobby._selection_adapter
	assert(adapter != null and adapter.independent_selection)
	adapter._apply_choice_resource_ids(lobby._slot, {"fighter": "sasuke" if lobby._slot == 0 else "rifagu", "helper": "you" if lobby._slot == 0 else "kon"})
	adapter._on_local_confirmation_timeout(lobby._slot)
	adapter._on_local_confirmation_timeout(lobby._slot)
	while lobby._selection_active:
		await get_tree().process_frame
	if lobby._slot == 0:
		lobby._on_commit_setup_pressed()
		lobby._map_adapter._select("木叶村")
		lobby._map_adapter._confirm()
