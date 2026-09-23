extends SceneTree

const Lobby := preload("res://online_lobby.gd")
const EPOCH := "3fa85f64-5717-4562-b3fc-2c963f66afa6"

class FakeCoordinator:
	extends RefCounted
	var pause_requests := 0
	var resume_requests := 0
	var pause_responses: Array[Dictionary] = []
	var resume_responses: Array[Dictionary] = []
	var intro_requests := 0
	var close_calls := 0
	var close_reason := ""

	func request_pause() -> String:
		pause_requests += 1
		return ""

	func request_resume() -> String:
		resume_requests += 1
		return ""

	func respond_pause(request_id: String, accepted: bool) -> String:
		pause_responses.append({"id": request_id, "accepted": accepted})
		return ""

	func respond_resume(request_id: String, accepted: bool) -> String:
		resume_responses.append({"id": request_id, "accepted": accepted})
		return ""

	func request_intro_skip() -> String:
		intro_requests += 1
		return ""

	func close(reason: String = "") -> void:
		close_calls += 1
		close_reason = reason


class FakeBridge:
	extends RefCounted
	var next_token := 0
	var owner_token := -1
	var callback: Callable
	var current_snapshot: Dictionary = {}
	var last_snapshot: Dictionary = {}
	var update_count := 0
	var rejected_updates := 0
	var rejected_unregistrations := 0

	func register(next_callback: Variant) -> int:
		next_token += 1
		owner_token = next_token
		callback = next_callback
		current_snapshot.clear()
		return owner_token

	func update(snapshot_json: String, token: int) -> bool:
		if token != owner_token:
			rejected_updates += 1
			return false
		var parsed: Variant = JSON.parse_string(snapshot_json)
		if not parsed is Dictionary:
			return false
		current_snapshot = parsed.duplicate(true)
		last_snapshot = parsed.duplicate(true)
		update_count += 1
		return true

	func unregister(token: int) -> bool:
		if token != owner_token:
			rejected_unregistrations += 1
			return false
		owner_token = -1
		callback = Callable()
		current_snapshot.clear()
		return true

	func fire(action: String, request_id: String = "", revision: int = -1) -> void:
		if not callback.is_valid() or current_snapshot.is_empty():
			return
		var action_revision := int(current_snapshot.get("revision", -1)) if revision < 0 else revision
		callback.call([
			action,
			str(current_snapshot.get("session", "")),
			action_revision,
			request_id,
		])


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var bridge := FakeBridge.new()
	var first := await _new_lobby(bridge)
	var first_coordinator := _start_fake_match(first, "hud-session-one")
	assert(first._match_started and first._web_match_hud_registered)
	assert(not first._match_hud.visible, "Acknowledged shell HUD should take over from the native fallback")
	assert(bridge.current_snapshot.get("active") == true)
	assert(bridge.current_snapshot.get("session") == "hud-session-one:1")
	assert(bridge.current_snapshot.has("revision"))

	var unchanged_updates := bridge.update_count
	first._push_web_match_hud()
	assert(bridge.update_count == unchanged_updates, "Unchanged snapshots should not be serialized and pushed every frame")

	first._pause_button.disabled = true
	first._push_web_match_hud()
	var disabled_revision := int(bridge.current_snapshot.get("revision", -1))
	bridge.fire("pause")
	assert(first_coordinator.pause_requests == 0, "A disabled native pause control accepted a shell click")
	first._pause_button.disabled = false
	first._push_web_match_hud()
	var pause_revision := int(bridge.current_snapshot.get("revision", -1))
	bridge.fire("pause")
	assert(first_coordinator.pause_requests == 1, "Shell pause action did not use the existing pause handler")
	bridge.fire("pause", "", pause_revision)
	assert(first_coordinator.pause_requests == 1, "A duplicate revision repeated the pause action")
	assert(pause_revision > disabled_revision)

	first._on_pause_changed(true)
	first._sync_match_hud_controls()
	first._push_web_match_hud()
	assert(bridge.current_snapshot.get("canResume") == true)
	bridge.fire("resume")
	assert(first_coordinator.resume_requests == 1, "Shell resume action did not use the existing pause handler")

	first._show_control_request("pause", {"id": "pause-request-7"})
	first._sync_match_hud_controls()
	first._push_web_match_hud()
	assert(bridge.current_snapshot.get("pauseRequest", {}).get("id") == "pause-request-7")
	first._control_accept_button.disabled = true
	first._push_web_match_hud()
	bridge.fire("accept_pause", "pause-request-7")
	assert(first_coordinator.pause_responses.is_empty(), "A disabled reply button accepted a shell response")
	first._control_accept_button.disabled = false
	first._push_web_match_hud()
	bridge.fire("accept_pause", "pause-request-7")
	assert(first_coordinator.pause_responses.size() == 1)
	assert(first_coordinator.pause_responses[0] == {"id": "pause-request-7", "accepted": true})

	first._on_recovery_changed("recovering:heartbeat_timeout")
	first._push_web_match_hud()
	assert(bridge.current_snapshot.get("status") == "网络状态：正在恢复连接",
		"Already-humanized recovery status was mapped a second time")

	first._intro_skip_button.visible = true
	first._sync_match_hud_controls()
	first._push_web_match_hud()
	bridge.fire("skip_intro")
	assert(first_coordinator.intro_requests == 1, "Shell intro skip did not use the existing request handler")
	first._intro_skip_button.visible = false
	first._push_web_match_hud()
	bridge.fire("skip_intro")
	assert(first_coordinator.intro_requests == 1, "Shell intro skip bypassed the hidden native control gate")

	var second := await _new_lobby(bridge)
	var second_coordinator := _start_fake_match(second, "hud-session-two")
	var second_owner := bridge.owner_token
	first._unregister_web_match_hud()
	assert(bridge.owner_token == second_owner and bridge.current_snapshot.get("active") == true,
		"A stale lobby clear replaced the current shell HUD owner")
	assert(bridge.rejected_updates > 0 and bridge.rejected_unregistrations > 0)
	bridge.fire("pause")
	assert(second_coordinator.pause_requests == 1, "Stale cleanup removed the newer shell owner's callback")

	var native := await _new_lobby(null)
	var native_coordinator := _start_fake_match(native, "native-fallback")
	assert(native._match_hud.visible and not native._web_match_hud_registered,
		"Native or unavailable bridge must retain the compact fallback HUD")
	assert(native._match_hud.offset_left == -220 and native._match_hud.offset_top == 40)
	native._pause_button.pressed.emit()
	assert(native_coordinator.pause_requests == 1, "Native fallback pause action stopped working")

	assert(second._web_match_hud_registered)
	second._unregister_web_match_hud()
	assert(bridge.owner_token == -1 and not bridge.last_snapshot.get("active", true),
		"Match lifecycle cleanup did not publish an inactive shell snapshot and unregister its owner")

	assert(first._register_web_match_hud(), "An active match could not register the shell controls again")
	bridge.fire("exit")
	assert(first_coordinator.close_calls == 0, "The first exit click bypassed the native confirmation step")
	assert(bridge.current_snapshot.get("exitLabel") == "再点一次确认退出")
	bridge.fire("exit")
	for _frame in 4:
		await process_frame
	assert(first_coordinator.close_calls == 1 and first_coordinator.close_reason == "local_exit",
		"Confirmed shell exit did not invoke the existing match close path exactly once")
	assert(not first._match_started and bridge.owner_token == -1)
	assert(bridge.last_snapshot.get("active") == false,
		"Exit cleanup did not clear the shell controls before unregistering")

	second.queue_free()
	native.queue_free()
	first.queue_free()
	await process_frame
	print("ONLINE_LOBBY_WEB_HUD_SMOKE_OK shell_actions=true native_gates=true stale_revision=true stale_owner=true recovery_status=true lifecycle_clear=true")
	quit(0)


func _new_lobby(bridge: FakeBridge) -> OnlineLobby:
	var lobby: OnlineLobby = Lobby.new()
	lobby.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(lobby)
	await process_frame
	lobby._web_match_hud_bridge_override = bridge
	return lobby


func _start_fake_match(lobby: OnlineLobby, epoch: String) -> FakeCoordinator:
	lobby._starting_epoch = epoch
	lobby._lifecycle_generation = 1
	var fake := FakeCoordinator.new()
	lobby.coordinator = fake
	lobby._on_match_started(epoch, lobby._lifecycle_generation)
	lobby.set_physics_process(false)
	return fake
