extends SceneTree
const Coordinator := preload("res://online_match.gd")
const Session := preload("res://rollback_session.gd")
func _initialize() -> void:
	for slot in ["p1", "p2"]:
		var peer := Coordinator.new()
		peer.rollback = Session.new()
		peer.rollback.frontier = 100
		peer.local_slot = slot
		peer.profile = {"inputDelay": 2}
		peer._latest_remote_input_frame = 95
		var skipped := 0
		var advanced := 0
		for tick in 1100:
			if peer._should_pace_host(): skipped += 1
			else:
				advanced += 1
				peer._pacing_steps += 1
		assert(skipped > 0 and skipped * 10 <= advanced)
		peer._frame_advantage = 2.0
		peer._latest_remote_input_frame = 101
		assert(peer._pacing_active)
		peer._should_pace_host()
		assert(peer._pacing_active, "Hysteresis must retain pacing inside the dead band")
		peer._latest_remote_input_frame = 105
		for tick in 40: peer._should_pace_host()
		assert(not peer._pacing_active)
		peer._latest_remote_input_frame = 0
		for tick in 100: peer._should_pace_host()
		# Without successful simulation there is no accumulating stall budget.
		for tick in 100: assert(not peer._should_pace_host())
	print("ONLINE_HOST_PACING_SMOKE_OK symmetric=true stretch_max=10_percent hysteresis=true")
	quit()
