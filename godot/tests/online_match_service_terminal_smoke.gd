extends SceneTree

const Coordinator = preload("res://online_match.gd")
const MATCH_EPOCH := "3fa85f64-5717-4562-b3fc-2c963f66afa6"


class FakeRoom extends Node:
	var terminal_state: Dictionary = {}
	var command_calls := 0
	var refresh_calls := 0

	func command(_operation: Dictionary) -> Dictionary:
		command_calls += 1
		return {"error": "stale_epoch", "uncertain": false}

	func refresh_state() -> Dictionary:
		refresh_calls += 1
		return terminal_state.duplicate(true)

	func get_room_state() -> Dictionary:
		return terminal_state.get("state", {}).duplicate(true)


func _initialize() -> void:
	var coordinator := _coordinator()
	for reason in ["aborted", "result_mismatch", "participant_left", "start_timeout", "initial_state_mismatch"]:
		var outcome: Dictionary = coordinator._service_terminal_outcome({"phase": "lobby", "lastResult": {
			"epoch": MATCH_EPOCH, "reason": reason, "winner": null,
		}})
		assert(outcome.get("kind") == "no_winner" and outcome.get("reason") == reason,
			"Known no-winner service terminal was not recognized: " + reason)
	var stale_epoch: Dictionary = coordinator._service_terminal_outcome({"phase": "lobby", "lastResult": {
		"epoch": "a different epoch", "reason": "aborted", "winner": null,
	}})
	assert(stale_epoch.is_empty(), "A terminal result from another epoch was accepted")
	var unknown_reason: Dictionary = coordinator._service_terminal_outcome({"phase": "lobby", "lastResult": {
		"epoch": MATCH_EPOCH, "reason": "future_server_reason", "winner": null,
	}})
	assert(unknown_reason.is_empty(), "An unrecognized terminal reason was accepted")
	var has_winner: Dictionary = coordinator._service_terminal_outcome({"phase": "lobby", "lastResult": {
		"epoch": MATCH_EPOCH, "reason": "participant_left", "winner": 0,
	}})
	assert(has_winner.is_empty(), "A winner-bearing leave result was accepted as no-winner")
	var agreed: Dictionary = coordinator._service_terminal_outcome({"phase": "lobby", "lastResult": {
		"epoch": MATCH_EPOCH, "reason": "agreed", "winner": 1.0,
	}})
	assert(agreed.get("kind") == "agreed" and agreed.get("winner") == 1,
		"Agreed winner JSON float was not normalized")
	var closed: Dictionary = coordinator._service_terminal_outcome({"phase": "closed"})
	assert(closed.get("kind") == "room_unavailable", "Closed room was not a terminal outcome")
	var expired: Dictionary = coordinator._service_terminal_outcome({"error": "room_expired", "httpStatus": 410})
	assert(expired.get("kind") == "room_unavailable", "Expired room was not a terminal outcome")
	var transient: Dictionary = coordinator._service_terminal_outcome({"error": "http_transport_failed", "httpStatus": 0})
	assert(transient.is_empty(), "Transient service loss was treated as permanent")

	var emitted: Array[Dictionary] = []
	coordinator.room_match_aborted.connect(func(report: Dictionary) -> void: emitted.append(report))
	coordinator._settle_service_abort({"kind": "diagnostic"}, expired)
	assert(emitted.size() == 1 and emitted[0].get("service_terminal") == "room_unavailable"
		and emitted[0].get("service_error") == "room_expired",
		"Room-unavailable settlement did not preserve the UI teardown reason")
	var already_finished := _coordinator()
	var terminal_reports: Array[Dictionary] = []
	already_finished.room_match_aborted.connect(func(report: Dictionary) -> void: terminal_reports.append(report))
	already_finished._settle_abort_terminal({"kind": "state_mismatch"}, agreed)
	assert(terminal_reports.size() == 1 and terminal_reports[0].get("service_terminal") == "match_already_finished"
		and terminal_reports[0].get("last_result", {}).get("reason") == "agreed",
		"An unrelated local abort misreported an agreed service result as cancellation")
	var matching_result := _coordinator()
	var committed: Array[Dictionary] = []
	matching_result.room_result_committed.connect(func(result: Dictionary) -> void: committed.append(result))
	var local_result := {"epoch": MATCH_EPOCH, "frame": 60, "winner": 1, "hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}
	matching_result._local_results[60] = local_result
	matching_result._remote_result = local_result.duplicate(true)
	matching_result._result_submission_started = true
	matching_result._settle_abort_terminal({"kind": "late_abort"}, agreed)
	assert(committed.size() == 1 and committed[0] == local_result,
		"A previously verified peer result was not committed after service agreement")
	call_deferred("_verify_submission_settlement")


func _verify_submission_settlement() -> void:
	var abort_room := FakeRoom.new()
	abort_room.terminal_state = {"state": {"phase": "lobby", "lastResult": {
		"epoch": MATCH_EPOCH, "reason": "participant_left", "winner": null,
	}}}
	root.add_child(abort_room)
	var abort_match := _coordinator()
	abort_match.room_client = abort_room
	abort_match._generation = 7
	var abort_reports: Array[Dictionary] = []
	abort_match.room_match_aborted.connect(func(report: Dictionary) -> void: abort_reports.append(report))
	await abort_match._submit_confirmed_abort({"kind": "peer_disconnect_timeout"}, 7)
	assert(abort_room.command_calls == 1 and abort_room.refresh_calls == 1,
		"Abort submission retried after refresh had already shown a terminal same-epoch result")
	assert(abort_reports.size() == 1 and abort_reports[0].get("service_terminal") == "match_aborted",
		"Abort submission did not settle the backend's participant-left result")

	var result_room := FakeRoom.new()
	result_room.terminal_state = {"state": {"phase": "lobby", "lastResult": {
		"epoch": MATCH_EPOCH, "reason": "start_timeout", "winner": null,
	}}}
	root.add_child(result_room)
	var result_match := _coordinator()
	result_match.room_client = result_room
	result_match._generation = 8
	var result_reports: Array[Dictionary] = []
	result_match.room_match_aborted.connect(func(report: Dictionary) -> void: result_reports.append(report))
	await result_match._submit_confirmed_result({"epoch": MATCH_EPOCH, "frame": 60, "winner": 0, "hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}, 8)
	assert(result_room.command_calls == 1 and result_room.refresh_calls == 1,
		"Result submission loop did not inspect a definitive rejection before retrying")
	assert(result_reports.size() == 1 and result_reports[0].get("service_terminal") == "match_aborted",
		"Result submission did not settle the backend's start-timeout result")
	print("ONLINE_MATCH_SERVICE_TERMINAL_OK no_winner_allowlist=true epoch_scoped=true room_unavailable=true rejected_abort_and_result_settle=true transient_not_terminal=true")
	abort_room.free()
	result_room.free()
	quit()


func _coordinator() -> RefCounted:
	var coordinator: RefCounted = Coordinator.new()
	coordinator.epoch = MATCH_EPOCH
	return coordinator
