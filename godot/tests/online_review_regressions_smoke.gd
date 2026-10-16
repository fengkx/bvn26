extends "res://tests/online_redundant_inputs_smoke.gd"

class ReviewPeer extends Coordinator:
	var sent := []
	func _peer_link_connected() -> bool: return true
	func _send_peer(kind: String, payload: Dictionary) -> bool:
		sent.append({"type": kind, "payload": payload.duplicate(true)})
		return true
	func _attempt_signaling_reconnect(_generation: int) -> void: pass
	func _start_hash(_snapshot: Dictionary) -> String: return "a".repeat(64)
	func save_state() -> Dictionary: return {}
	func _abort_local(kind: String, _details: Dictionary, _notify_peer: bool = true) -> String:
		error = kind
		running = false
		return kind
	func _maybe_finish_result() -> void: pass

func _initialize() -> void:
	_test_startup_queue()
	_test_deadline()
	_test_backpressure()
	_test_recovery_commit_barrier()
	_test_lockstep_recovery()
	_test_diagnostic_cleanup.call_deferred()

func _test_startup_queue() -> void:
	for kind in ["match_ready", "match_abort"]:
		var peer := ReviewPeer.new()
		peer.sparse_saves = true
		peer.checkpoint_stride = 2
		peer.receive_peer_message("reliable", "match_abort", {"epoch": "retired"}, 1)
		peer.receive_peer_message("reliable", kind, {
			"epoch": "current",
			"initialHash": "a".repeat(64),
			"sparseSaves": true,
			"checkpointStride": 2,
		}, 1)
		assert(peer._received_sequences.is_empty() and peer.error.is_empty())
		peer.epoch = "current"
		peer._drain_early_epoch_messages()
		assert(peer._early_epoch_messages.is_empty())
		if kind == "match_ready": assert(peer._peer_ready and peer.error.is_empty())
		else: assert(peer.error == "peer_abort")
		peer.close()
	var mismatch := ReviewPeer.new()
	mismatch.sparse_saves = true
	mismatch.checkpoint_stride = 2
	mismatch.epoch = "current"
	mismatch._receive_match_ready({
		"epoch": "current",
		"initialHash": "a".repeat(64),
		"sparseSaves": false,
		"checkpointStride": 1,
	})
	assert(mismatch.error == "checkpoint_policy_mismatch")
	mismatch.close()

func _test_deadline() -> void:
	var peer := ReviewPeer.new()
	var now := int(Time.get_unix_time_from_system() * 1000)
	peer._room_state = {"match": {"deadline": now + 90_000}}
	var remaining := peer._startup_deadline_ms() - Time.get_ticks_msec()
	assert(remaining > 89_000 and remaining <= 90_000, "Worker budget must not be capped at 30s")
	peer._room_state.match.deadline = now - 1
	assert(peer._startup_deadline_ms() <= Time.get_ticks_msec(), "Expired preparation must not receive a new budget")
	peer.close()

func _test_backpressure() -> void:
	var peer := ReviewPeer.new()
	peer.epoch = "test"
	peer.local_slot = "p1"
	peer.remote_slot = "p2"
	peer.profile = {"inputDelay": 0, "predictionWindow": 6}
	peer.rollback = Session.new()
	peer.peer_transport = Transport.new()
	peer.running = true
	peer._configured = true
	peer._process_now_ms = 0
	assert(peer.rollback.configure(Adapter.new(), "test", 6, 80).is_empty())
	var held := Session._neutral()
	# ACK-only loss can persist even while remote inputs keep arriving.
	for frame in range(1, 65):
		assert(peer.rollback.receive("test", "p2", frame, held).is_empty())
		assert(peer._sample_local_once(held))
		assert(peer.rollback.step().is_empty())
	assert(peer._unacked_inputs.size() == 64)
	assert(peer.process_tick(100, held).is_empty())
	assert(peer.rollback.frontier == 64 and peer._unacked_inputs.size() == 64)
	assert(peer.peer_transport.packets.back().payload.inputs.size() == 64)
	peer.receive_peer_message("input", "input_batch", {"epoch": "test", "ack": 64, "inputs": []}, 1)
	assert(peer.process_tick(133, held).is_empty())
	assert(peer.rollback.frontier == 65 and peer._unacked_inputs.size() == 1)
	peer.close()

class ReentrantCommitPeer extends ReviewPeer:
	func _send_peer(kind: String, payload: Dictionary) -> bool:
		sent.append({"type": kind, "payload": payload.duplicate(true)})
		if kind == "recovery_commit":
			assert(bool(_recovery_state.get("commit_pending", false)),
				"commit_pending must be set before recovery_commit leaves the host")
			_receive_recovery_commit_ack({
				"epoch": epoch, "recovery_id": _recovery_id, "frame": int(payload.frame),
				"hash": str(payload.hash),
			})
		return true


func _test_recovery_commit_barrier() -> void:
	var host := ReentrantCommitPeer.new()
	host.epoch = "test"
	host.local_slot = "p1"
	host.remote_slot = "p2"
	host.recovering = true
	host._recovery_id = "test:1"
	host._recovery_state = {"requested_frame": 30, "local_hash": "b".repeat(64)}
	host._receive_recovery_compare({
		"epoch": "test", "recovery_id": "test:1", "frame": 30, "hash": "b".repeat(64),
	})
	assert(not host.recovering and host.error.is_empty())
	assert(host._last_completed_recovery_id == "test:1")
	host.close()


func _test_lockstep_recovery() -> void:
	for delay in [0, 4]:
		var peers := []
		for index in 2:
			var peer := ReviewPeer.new()
			peer.epoch = "test"
			peer.profile = {"inputDelay": delay, "predictionWindow": 0}
			peer.local_slot = "p1" if index == 0 else "p2"
			peer.remote_slot = "p2" if index == 0 else "p1"
			peer.rollback = Session.new()
			# Neither sparse_saves nor retain_hash_history is enabled.
			assert(peer.rollback.configure(Adapter.new(), "test", 0, delay + 2, delay).is_empty())
			peer.peer_transport = Transport.new()
			peer.running = true
			peer._process_now_ms = 0
			for frame in range(1, 61 - index):
				for slot in ["p1", "p2"]:
					assert(peer.rollback.receive("test", slot, frame, Session._neutral()).is_empty())
				assert(peer.rollback.step().is_empty())
			# Guest missed frame 60; recovery must compare the retained frame 30.
			peer._local_inputs[60] = Session._neutral()
			peer._unacked_inputs[60] = Session._neutral()
			assert(peer.rollback.receive("test", peer.local_slot, 60, Session._neutral()).is_empty())
			peers.append(peer)
		peers[0]._begin_recovery("heartbeat_timeout", 5_000)
		peers[0]._check_recovery_deadline(17_560)
		assert(peers[0].error.is_empty(), "17.56s page suspension must leave time to recover")
		for _round in 10:
			for peer in peers:
				peer._process_now_ms = 17_560 + _round * 500
				if peer.recovering: peer._send_recovery_sync(peer._process_now_ms)
			for index in 2:
				var peer: ReviewPeer = peers[index]
				var messages := peer.sent.duplicate()
				peer.sent.clear()
				for message in messages:
					peers[1 - index]._dispatch_peer_message("reliable", message.type, message.payload)
		assert(peers[0].error.is_empty() and peers[1].error.is_empty(), str([peers[0].error, peers[1].error, peers[0]._recovery_state, peers[1]._recovery_state]))
		assert(not peers[0].recovering and not peers[1].recovering)
		assert(peers[0]._last_completed_recovery_id == "test:1")
		assert(peers[1]._last_completed_recovery_id == "test:1")
		for index in 2:
			var peer: ReviewPeer = peers[index]
			peer._send_input_packet()
			for packet in peer.peer_transport.packets:
				peers[1 - index]._receive_input_packet(packet.payload)
		assert(peers[1].rollback.step().is_empty())
		assert(State.fingerprint(peers[0].rollback.state_at(60)) == State.fingerprint(peers[1].rollback.state_at(60)))
		for peer in peers:
			for packet in peer.peer_transport.packets:
				assert(packet.type == "input_batch" and packet.payload.ack >= delay)
			peer.close()

func _test_diagnostic_cleanup() -> void:
	var fixture = preload("res://tests/rollback_fixture.gd").create(self)
	fixture.battle.begin_replay()
	assert(fixture.game.diagnostics.replaying)
	fixture.battle.close()
	assert(not fixture.game.diagnostics.replaying and not fixture.battle.checkpoint.replaying)
	fixture.game.diagnostics.replaying = true
	fixture.game.diagnostics.end_match("interrupted_replay")
	assert(not fixture.game.diagnostics.replaying)
	preload("res://tests/rollback_fixture.gd").dispose(fixture.game, fixture.battle)
	print("ONLINE_REVIEW_REGRESSIONS_SMOKE_OK startup_deadline_epoch_backpressure_lockstep_loss_suspend_cleanup=true")
	quit()
