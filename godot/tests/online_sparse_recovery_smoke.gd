extends "res://tests/rollback_batched_correction_smoke.gd"

const Coordinator := preload("res://online_match.gd")


class RecordingCoordinator extends Coordinator:
	var sent := []

	func _send_peer(kind: String, payload: Dictionary) -> bool:
		sent.append({"kind": kind, "payload": payload})
		return true


func _run() -> void:
	for policies in [[false, true], [true, false], [true, true]]:
		var sessions := []
		for index in range(2):
			var session := _make()
			session.sparse_saves = policies[index]
			session.retain_hash_history = true
			for frame in range(1, 61 - index):
				for slot in ["p1", "p2"]:
					assert(session.receive("batch", slot, frame, _buttons(frame % 2 == 0)).is_empty())
				assert(session.step().is_empty())
			sessions.append(session)
		var coordinator := RecordingCoordinator.new()
		coordinator.rollback = sessions[0]
		coordinator.local_slot = "p1"
		coordinator.epoch = "batch"
		coordinator._recovery_id = "batch:1"
		coordinator._recovery_state = {"remote_sync": {"confirmedFrame": sessions[1].latest_hash_frame(), "hashFloor": sessions[1].hash_floor()}}
		coordinator._propose_recovery_comparison()
		assert(coordinator.error.is_empty())
		assert(coordinator.sent.size() == 1)
		assert(coordinator.sent[0].payload.frame == 30)
		assert(coordinator.sent[0].payload.hash == State.fingerprint(sessions[1].state_at(30)))
		for session in sessions: _dispose(session)
	print("ONLINE_SPARSE_RECOVERY_SMOKE_OK confirmed_60_59_compares_30=true mixed_policies=true")
	quit()
