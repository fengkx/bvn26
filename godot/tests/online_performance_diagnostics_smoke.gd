extends SceneTree

const Perf := preload("res://online_performance.gd")
const Coordinator := preload("res://online_match.gd")
const Rollback := preload("res://rollback_session.gd")
const State := preload("res://simulation_state.gd")


class FakeAdapter extends RefCounted:
	var frame := 0

	func save_state() -> Dictionary:
		return State.pack_state("online-performance-smoke", frame, {"fixture": {"frame": frame}})

	func validate_state(snapshot: Dictionary) -> String:
		return State.validate_snapshot(snapshot, "online-performance-smoke", ["fixture"])

	func load_state(snapshot: Dictionary) -> String:
		frame = int(snapshot.frame)
		return ""

	func advance(next_frame: int, _players: Dictionary) -> String:
		frame = next_frame
		return ""


class FakeDiagnostics extends RefCounted:
	var events: Array[Dictionary] = []

	func push_event(event_type: String, payload: Dictionary) -> Dictionary:
		var event := {"type": event_type, "payload": payload.duplicate(true)}
		events.append(event)
		return event


class FakeGame extends Node:
	var diagnostics := FakeDiagnostics.new()


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	_test_bounded_samples_and_window_reset()
	_test_exclusive_wait_accounting()
	_test_rollback_work_and_sync_metrics()
	_test_rollback_profile_counts()
	_test_optional_diagnostics_and_teardown()
	_test_telemetry_stays_out_of_causal_snapshot()
	print("ONLINE_PERFORMANCE_DIAGNOSTICS_OK bounded_samples=true window_reset=true exclusive_waits=true rollback_work=true sync_metrics=true optional_diagnostics=true teardown=true snapshot_isolation=true")
	quit()


func _test_bounded_samples_and_window_reset() -> void:
	var performance = Perf.new()
	performance.start(0, 0, 0, true, {"available": false})
	for elapsed_usec in range(125):
		performance.record_simulation_step(elapsed_usec)
	var first: Dictionary = performance.collect_summary(1_000, 1_000_000, 30, 30, {}, {"available": false})
	assert(first.simulationStepCount == 125)
	assert(first.simulationStepSampleCount == 120)
	assert(first.simulationStepSampleDropped == 5 and first.simulationStepSamplesTruncated)
	assert(first.simulationStepP95Us == 118 and first.simulationStepP99Us == 123)
	assert(first.matchTotals.work.simulation_step.count == 125)
	performance.record_simulation_step(900)
	var second: Dictionary = performance.collect_summary(2_000, 2_000_000, 60, 60, {}, {"available": false})
	assert(second.simulationStepCount == 1 and second.simulationStepSampleCount == 1)
	assert(second.simulationStepP95Us == 900 and second.simulationStepSampleDropped == 0)
	assert(second.matchTotals.work.simulation_step.count == 126)
	assert(second.network.rttAvailable == false and second.network.rttMs == null)
	performance.stop()
	performance.stop()


func _test_exclusive_wait_accounting() -> void:
	var performance = Perf.new()
	performance.start(1_000, 0, 0, true, {"available": false})
	performance.set_wait("clock", 1_010)
	performance.set_wait("input", 1_035)
	var summary: Dictionary = performance.collect_summary(1_100, 1_100_000, 0, 0, {}, {"available": false})
	assert(summary.waitMs.clock == 25)
	assert(summary.waitMs.input == 65)
	assert(summary.waitMs.values().reduce(func(total: int, value: int) -> int: return total + value, 0) == 90)
	assert(summary.waitCount.clock == 1 and summary.waitCount.input == 1)
	performance.stop()


func _test_rollback_work_and_sync_metrics() -> void:
	var performance = Perf.new()
	var baseline := _rollback_counters()
	baseline.save_count = 1 # configure's initial checkpoint is before the window baseline.
	performance.start(0, 0, 0, true, {"available": false}, {"available": true, "totals": baseline})
	performance.record_sync_tick(2, 1, 6, 3)
	performance.record_transport_drain(3, 1)
	performance.record_input_arrival_lead(-2)
	var current := _rollback_counters()
	current.advance_count = 1
	current.advance_us = 100
	current.save_count = 4
	current.save_us = 400
	current.validate_count = 2
	current.validate_us = 20
	current.copy_count = 3
	current.copy_us = 30
	current.load_count = 1
	current.load_us = 50
	current.replay_advance_count = 2
	current.replay_advance_us = 200
	current.replay_save_count = 2
	current.rebuild_count = 1
	current.rebuild_us = 10
	var summary: Dictionary = performance.collect_summary(1_000, 1_000_000, 6, 6, {},
		{"available": false}, {"available": true, "totals": current})
	assert(summary.schemaVersion == 2)
	assert(summary.rollbackWork.available)
	assert(summary.rollbackWork.windowDelta.advance_count == 1)
	assert(summary.rollbackWork.windowDelta.save_count == 3)
	assert(summary.rollbackWork.windowDelta.replay_save_count == 2)
	assert(summary.rollbackWork.windowDelta.saves_skipped_count == 0)
	assert(summary.sync.ticks.remoteMessages == 2 and summary.sync.ticks.corrections == 1)
	assert(summary.sync.ticks.remoteMessagesPerTick.max == 2)
	assert(summary.sync.transportDrains.count == 1)
	assert(summary.sync.transportDrains.messagesDelivered == 3)
	assert(summary.sync.transportDrains.corrections == 1)
	assert(summary.sync.inputArrivalLead.p50 == -2)
	assert(summary.sync.frameAdvantage.p50 == 3)
	assert(summary.matchTotals.sync.ticks.count == 1)
	performance.stop()


func _rollback_counters() -> Dictionary:
	return {
		"advance_count": 0, "advance_us": 0,
		"save_count": 0, "save_us": 0,
		"validate_count": 0, "validate_us": 0,
		"copy_count": 0, "copy_us": 0,
		"load_count": 0, "load_us": 0,
		"replay_advance_count": 0, "replay_advance_us": 0,
		"replay_save_count": 0, "saves_skipped_count": 0,
		"rebuild_count": 0, "rebuild_us": 0,
	}


func _test_rollback_profile_counts() -> void:
	var rollback = Rollback.new()
	var adapter := FakeAdapter.new()
	# Exercise retained snapshot anchors; lockstep deliberately omits these saves.
	assert(rollback.configure(adapter, "copy-profile", 1, 3).is_empty())
	var configured := rollback.profile_counters()
	assert(configured.save_count == 1)
	assert(configured.copy_count == 1)
	var held := _neutral_input()
	var first_step_copy_delta := 0
	for frame in range(1, 4):
		assert(rollback.sample_local("p1", frame, held).get("error", "").is_empty())
		assert(rollback.receive("copy-profile", "p2", frame, held).is_empty())
		var before_step := int(rollback.profile_counters().copy_count)
		assert(rollback.step().is_empty())
		var after_step := int(rollback.profile_counters().copy_count)
		if frame == 3:
			assert(after_step - before_step == first_step_copy_delta + 2,
				"Advancing the retained floor must count both input-anchor copies")
		else:
			first_step_copy_delta = after_step - before_step
	var before_local_packet := int(rollback.profile_counters().copy_count)
	assert(rollback.sample_local("p1", 4, held).get("error", "").is_empty())
	var after_local_packet := int(rollback.profile_counters().copy_count)
	assert(after_local_packet - before_local_packet == 2,
		"Local input and its packet must count two dictionary copies")
	assert(rollback.receive("copy-profile", "p2", 4, held).is_empty())
	var after_remote_input := int(rollback.profile_counters().copy_count)
	assert(after_remote_input - after_local_packet == 1,
		"Accepted remote input must count its owned dictionary copy")


	for frame in range(4, 33):
		if frame > 4:
			assert(rollback.sample_local("p1", frame, held).get("error", "").is_empty())
			assert(rollback.receive("copy-profile", "p2", frame, held).is_empty())
		var old_floor: int = rollback.oldest_frame()
		var before_step := int(rollback.profile_counters().copy_count)
		assert(rollback.step().is_empty())
		var anchor_copies := 2 if rollback.oldest_frame() > old_floor else 0
		assert(int(rollback.profile_counters().copy_count) - before_step == first_step_copy_delta + anchor_copies)
	assert(rollback.oldest_frame() == 30)


func _neutral_input() -> Dictionary:
	var held := {}
	for button in Rollback.BUTTONS:
		held[button] = false
	return held


func _test_optional_diagnostics_and_teardown() -> void:
	var performance = Perf.new()
	performance.stop()
	performance.stop()
	performance.record_input_receive(10, 1, 2)
	performance.set_wait("input", 5)
	performance.set_page_visible(false, 5)
	assert(not performance.active)
	var coordinator = Coordinator.new()
	coordinator._publish_performance_summary({"schemaVersion": 1})
	var game := FakeGame.new()
	coordinator.game = game
	coordinator._publish_performance_summary({"schemaVersion": 1})
	assert(game.diagnostics.events.size() == 1)
	assert(game.diagnostics.events[0].type == "online_performance")
	game.free()
	coordinator.game = null
	coordinator._performance.start(10, 0, 0, true, {"available": false})
	coordinator.close("test_teardown")
	assert(not coordinator._performance.active)
	assert(coordinator.performance_report().get("available", false))
	coordinator.close()


func _test_telemetry_stays_out_of_causal_snapshot() -> void:
	var adapter := FakeAdapter.new()
	var rollback = Rollback.new()
	assert(rollback.configure(adapter, "smoke-epoch", 2, 4) == "")
	var causal_snapshot := rollback.state_at(0)
	var performance = Perf.new()
	performance.start(0, rollback.frontier, rollback.confirmed, true, {"available": false})
	performance.begin_tick(1_000, rollback.frontier)
	performance.finish_tick(1_100, rollback.frontier)
	performance.set_wait("input", 10)
	performance.collect_summary(1_000, 1_100, rollback.frontier, rollback.confirmed, {}, {"available": false})
	assert(rollback.state_at(0) == causal_snapshot)
	assert(not rollback.state_at(0).has("performance"))
	performance.stop()
