extends SceneTree

const Coordinator := preload("res://online_match.gd")
const Session := preload("res://rollback_session.gd")


func _initialize() -> void:
	var coordinator := Coordinator.new()
	coordinator.rollback = Session.new()
	coordinator.rollback.frontier = 100
	coordinator.local_slot = "p1"
	coordinator.profile = {"inputDelay": 2}
	coordinator._latest_remote_input_frame = 95
	assert(not coordinator._should_pace_host())
	coordinator.host_pacing = true
	var skipped := []
	for tick in range(12):
		if coordinator._should_pace_host(): skipped.append(tick)
	assert(skipped == [0, 3, 6, 9])
	for condition in ["guest", "pause", "recovery", "control", "close", "unknown"]:
		coordinator.local_slot = "p2" if condition == "guest" else "p1"
		coordinator.paused = condition == "pause"
		coordinator.recovering = condition == "recovery"
		coordinator._pause_state = {"id": "pending"} if condition == "control" else {}
		coordinator._latest_remote_input_frame = -1 if condition == "unknown" else (103 if condition == "close" else 95)
		for _tick in range(6): assert(not coordinator._should_pace_host())
	print("ONLINE_HOST_PACING_SMOKE_OK cooldown=2 guest_control_pause_recovery_excluded=true")
	quit()
