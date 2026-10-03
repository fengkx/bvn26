extends SceneTree

const Coordinator := preload("res://online_match.gd")
const Session := preload("res://rollback_session.gd")
const State := preload("res://simulation_state.gd")
const Adapter := preload("res://tests/rollback_batched_correction_smoke.gd").Adapter


class Game extends Node:
	var physics_tick := 6
	var ko_terminal_pending := false
	var diagnostics: Object


func _initialize() -> void:
	_run.call_deferred()


func _make_session(remote_slot: String, predicted: bool) -> RefCounted:
	var session := Session.new()
	var adapter := Adapter.new()
	adapter.session = session
	assert(session.configure(adapter, "batch", 8, 16).is_empty())
	for frame in range(1, 7):
		for slot in ["p1", "p2"]:
			if predicted and slot == remote_slot: continue
			var held := Session._neutral()
			held.attack = slot == remote_slot and frame % 2 == 0
			assert(session.receive("batch", slot, frame, held).is_empty())
		assert(session.step().is_empty())
	return session


func _run() -> void:
	for kind in ["state_hash", "result", "pause_request", "resume_commit", "recovery_sync", "invalid_input"]:
		var match_coordinator := Coordinator.new()
		var game := Game.new()
		match_coordinator.game = game
		match_coordinator.running = true
		match_coordinator.epoch = "batch"
		match_coordinator.local_slot = "p2" if kind == "resume_commit" else "p1"
		match_coordinator.remote_slot = "p1" if kind == "resume_commit" else "p2"
		match_coordinator._next_hash_frame = 6
		var session := _make_session(match_coordinator.remote_slot, true)
		var reference := _make_session(match_coordinator.remote_slot, false)
		match_coordinator.rollback = session
		var expected: Dictionary = reference.state_at(6)
		var digest := State.fingerprint(expected)
		var reports: Array[Dictionary] = []
		match_coordinator.diagnostic_abort.connect(func(report: Dictionary) -> void: reports.append(report))
		match_coordinator._on_transport_message_drain_started()
		for frame in range(1, 7):
			var held := Session._neutral()
			held.attack = frame % 2 == 0
			match_coordinator.receive_peer_message("reliable", "input_frame", {"frame": frame, "held": held}, frame)
		assert(session.rollback_count == 0 and session._dirty_from == 2)
		match kind:
			"state_hash":
				match_coordinator.receive_peer_message("reliable", "state_hash", {"frame": 6, "hash": digest}, 7)
				assert(session.rollback_count == 0, "A remote hash should wait for the batch to settle")
			"result":
				match_coordinator.receive_peer_message("reliable", "result", {"epoch": "batch", "frame": 6, "hash": digest, "winner": null}, 7)
				assert(session.rollback_count == 0 and match_coordinator._remote_result.hash == digest)
			"pause_request":
				match_coordinator.pause_requested.connect(func(_payload: Dictionary) -> void:
					assert(session._dirty_from < 0 and session._adapter.score == expected.owners.score))
				match_coordinator.receive_peer_message("reliable", "control", {"action": kind, "id": "pause", "frame": 6}, 7)
			"resume_commit":
				match_coordinator.paused = true
				match_coordinator._resume_state = {"id": "resume", "proposal_frame": 6, "local_ready_hash": digest}
				match_coordinator.receive_peer_message("reliable", "control", {"action": kind, "id": "resume", "frame": 6, "hash": digest, "paused_ms": 0}, 7)
				assert(not match_coordinator.paused and session._dirty_from < 0)
			"recovery_sync":
				match_coordinator.receive_peer_message("reliable", kind, {"epoch": "batch", "recovery_id": "",
					"frontier": 6, "confirmed": 6, "oldest": 0, "hashFloor": 0, "confirmedFrame": 0, "confirmedHash": State.fingerprint(reference.state_at(0))}, 7)
				assert(match_coordinator.recovering and session._dirty_from < 0)
			"invalid_input":
				match_coordinator.receive_peer_message("reliable", "input_frame", {"frame": 2, "held": {}}, 7)
				assert(reports.size() == 1 and reports[0].details.pending_correction.dirty_from == 2)
				assert(reports[0].details.pending_correction.actual[match_coordinator.remote_slot].keys() == [2, 3, 4, 5, 6])
		match_coordinator._on_transport_message_drain_completed(7)
		if kind == "invalid_input":
			assert(session.rollback_count == 0 and not match_coordinator.running)
		else:
			assert(match_coordinator.error.is_empty(), match_coordinator.error)
			assert(session.rollback_count == 1 and session.settled() == 6)
			assert(State.first_difference(session.state_at(6), expected).is_empty())
			if kind == "state_hash":
				assert(match_coordinator._remote_hashes.is_empty(), "Corrected hash was not compared")
		print("ONLINE_BATCH_ORDERING_CASE_OK ", kind)
		session._adapter.session = null
		reference._adapter.session = null
		match_coordinator.rollback = null
		game.free()
	print("ONLINE_BATCHED_ORDERING_SMOKE_OK cases=6")
	quit()
