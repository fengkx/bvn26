extends SceneTree

const Coordinator = preload("res://online_match.gd")


class FakeRollback extends RefCounted:
	var frontier := 12
	var confirmed := 12
	var first_receivable := 5
	var last_receivable := 44

	func can_receive_frame(frame: int) -> bool:
		return frame >= first_receivable and frame <= last_receivable

	func oldest_frame() -> int:
		return first_receivable - 1

	func state_at(_frame: int) -> Dictionary:
		return {}

	func pending_correction() -> Dictionary:
		return {}


func _initialize() -> void:
	var coordinator := _guest()
	coordinator._receive_clock_sample({"frame": 13, "elapsed_ms": 429})
	assert(coordinator.error.is_empty() and coordinator._clock_samples[13] == 429,
		"Valid in-window host clock sample was rejected")
	coordinator._receive_clock_sample({"frame": 13, "elapsed_ms": 429})
	assert(coordinator.error.is_empty(), "Identical clock retransmission was not idempotent")
	coordinator._clock_samples[4] = 99
	coordinator._receive_clock_sample({"frame": 4, "elapsed_ms": 99})
	assert(coordinator.error.is_empty(), "Known old clock retransmission was not idempotent")

	coordinator = _guest()
	coordinator._receive_clock_sample({"frame": 13, "elapsed_ms": 429})
	coordinator._receive_clock_sample({"frame": 13, "elapsed_ms": 430})
	assert(coordinator.error == "conflicting_clock_sample", "Conflicting immutable clock sample was not rejected")

	coordinator = _guest()
	coordinator._receive_clock_sample({"frame": 45, "elapsed_ms": 1452})
	assert(coordinator.error == "clock_sample_outside_receive_window", "Far-future clock sample exceeded the receive capacity")

	coordinator = _guest()
	coordinator._receive_clock_sample({"frame": 4, "elapsed_ms": 99})
	assert(coordinator.error == "clock_sample_outside_receive_window", "Unknown sample below the retained window was accepted")
	print("ONLINE_CLOCK_SAMPLE_BOUNDS_OK valid=true retransmit_idempotent=true conflict_rejected=true old_and_future_bounds=true")
	quit()


func _guest() -> RefCounted:
	var coordinator: RefCounted = Coordinator.new()
	coordinator.local_slot = "p2"
	coordinator.remote_slot = "p1"
	coordinator.clock_authority_slot = "p1"
	coordinator.rollback = FakeRollback.new()
	coordinator.running = true
	coordinator._process_now_ms = 0
	return coordinator
