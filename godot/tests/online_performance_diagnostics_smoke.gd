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
	_test_optional_diagnostics_and_teardown()
	_test_telemetry_stays_out_of_causal_snapshot()
	print("ONLINE_PERFORMANCE_DIAGNOSTICS_OK bounded_samples=true window_reset=true exclusive_waits=true optional_diagnostics=true teardown=true snapshot_isolation=true")
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
