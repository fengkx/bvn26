extends SceneTree

const Lobby := preload("res://online_lobby.gd")
const EPOCH := "3fa85f64-5717-4562-b3fc-2c963f66afa6"


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	if not await _test_room_unavailable():
		return
	if not await _test_authoritative_finished_result():
		return
	if not await _test_normal_abort_returns_to_room():
		return
	if not await _test_abandon_uncertain_admission():
		return
	print("ONLINE_LOBBY_TERMINAL_UI_OK room_unavailable_clears_credentials=true authoritative_result_preserved=true ordinary_abort_returns=true admission_abandon_warns_and_clears=true")
	quit(0)


func _test_room_unavailable() -> bool:
	var lobby: OnlineLobby = await _new_lobby()
	_prepare_active_room(lobby)
	lobby._finish_room_match_abort({
		"service_terminal": "room_unavailable",
		"reason": "room_expired",
	}, EPOCH, lobby._lifecycle_generation)
	lobby._process(0.0)
	if not _expect(lobby._room_id.is_empty() and lobby.room_client.get_room_id().is_empty()
		and lobby._invite_token.is_empty() and lobby._slot == -1,
		"Room-unavailable outcome retained local room credentials"):
		return false
	if not _expect(lobby._last_result_text.contains("房间已不可用")
		and lobby._last_result_text.contains("未能从房间服务确认"),
		"Room-unavailable outcome claimed the match was cancelled or had no winner"):
		return false
	if not _expect(lobby._rematch_button.disabled and lobby._result_leave_button.text == "清理并返回标题菜单",
		"Room-unavailable outcome still offered a return to the old room"):
		return false
	lobby._rematch_button.pressed.emit()
	await process_frame
	if not _expect(lobby._match_view.visible and lobby._room_id.is_empty(),
		"Disabled rematch path reopened the unavailable room"):
		return false
	lobby._result_leave_button.pressed.emit()
	await process_frame
	if not _expect(not lobby._dialog.visible and not lobby._veil.visible,
		"Local cleanup action did not return to the title screen"):
		return false
	lobby.queue_free()
	await process_frame
	return true


func _test_authoritative_finished_result() -> bool:
	var lobby: OnlineLobby = await _new_lobby()
	var result := {"epoch": EPOCH, "reason": "agreed", "winner": 1}
	_prepare_active_room(lobby, {"phase": "lobby", "lastResult": result.duplicate(true)})
	lobby._finish_room_match_abort({
		"service_terminal": "match_already_finished",
		"reason": "result_mismatch",
		"last_result": result.duplicate(true),
	}, EPOCH, lobby._lifecycle_generation)
	lobby._process(0.0)
	if not _expect(lobby._last_result_text == "玩家 2 获胜"
		and lobby._result_status.text.contains("房间服务已确认这局结束"),
		"Authoritative server result was replaced by a no-winner abort message: %s / %s" % [lobby._last_result_text, lobby._result_status.text]):
		return false
	if not _expect(not lobby._rematch_button.disabled and lobby._room_id == "a".repeat(64),
		"An already-finished result should preserve the live room and allow returning to its lobby"):
		return false
	lobby.queue_free()
	await process_frame
	return true


func _test_normal_abort_returns_to_room() -> bool:
	var lobby: OnlineLobby = await _new_lobby()
	_prepare_active_room(lobby, {"phase": "lobby", "lastResult": {
		"epoch": EPOCH, "reason": "aborted", "winner": null,
	}})
	lobby._result_leave_button.text = "清理并返回标题菜单"
	lobby._finish_room_match_abort({
		"service_terminal": "match_aborted",
		"reason": "peer_disconnect_timeout",
	}, EPOCH, lobby._lifecycle_generation)
	lobby._process(0.0)
	if not _expect(lobby._last_result_text.begins_with("同步未完成，本局不记胜负")
		and lobby._rematch_button.text == "返回房间" and not lobby._rematch_button.disabled,
		"A confirmed no-winner abort did not allow returning to the room"):
		return false
	if not _expect(lobby._result_leave_button.text == "离开联机模式",
		"Normal abort retained the room-unavailable leave label"):
		return false
	lobby.queue_free()
	await process_frame
	return true


func _test_abandon_uncertain_admission() -> bool:
	var lobby: OnlineLobby = await _new_lobby()
	lobby._admission_uncertain = true
	lobby.room_client._pending_admission = {"kind": "create", "body": "pending"}
	lobby._set_admission_uncertain(true)
	lobby._home_view.visible = true
	lobby._dialog.visible = true
	lobby._veil.visible = true
	if not _expect(lobby._admission_abandon_button.visible
		and lobby._admission_uncertain_warning.visible
		and lobby._admission_uncertain_warning.text.contains("暂时无法确认请求结果")
		and lobby._admission_uncertain_warning.text.contains("返回将放弃此次请求")
		and lobby._admission_uncertain_warning.text.contains("已创建的空闲房间")
		and lobby._admission_uncertain_warning.text.contains("30 分钟后关闭"),
		"Uncertain admission did not explain its remote-room/expiry limit"):
		return false
	var generation_before := lobby._lifecycle_generation
	lobby._admission_abandon_button.pressed.emit()
	await process_frame
	if not _expect(lobby._lifecycle_generation > generation_before
		and lobby.room_client._pending_admission.is_empty()
		and lobby.room_client.get_room_id().is_empty()
		and not lobby._admission_uncertain and lobby._room_id.is_empty(),
		"Abandon did not invalidate lifecycle state and clear local admission credentials"):
		return false
	if not _expect(not lobby._dialog.visible and not lobby._veil.visible,
		"Uncertain admission abandon did not return to the title menu"):
		return false
	lobby.queue_free()
	await process_frame
	return true


func _new_lobby() -> OnlineLobby:
	var lobby: OnlineLobby = Lobby.new()
	root.add_child(lobby)
	await process_frame
	return lobby


func _prepare_active_room(lobby: OnlineLobby, state: Dictionary = {"phase": "active", "lastResult": null}) -> void:
	lobby._lifecycle_generation = 4
	lobby._starting_epoch = EPOCH
	lobby._terminal_pending_epoch = EPOCH
	lobby._terminal_finished_epoch = ""
	lobby._terminal_commit_queued_epoch = ""
	lobby._room_id = "a".repeat(64)
	lobby._invite_token = "b".repeat(43)
	lobby._slot = 0
	lobby.room_client._room_id = lobby._room_id
	lobby.room_client._session_token = "c".repeat(43)
	lobby.room_client._invite_token = lobby._invite_token
	lobby.room_client._slot = 0
	lobby.room_client._room_state = state.duplicate(true)
	lobby._room_state = state.duplicate(true)


func _expect(condition: bool, message: String) -> bool:
	if condition:
		return true
	push_error(message)
	quit(1)
	return false
