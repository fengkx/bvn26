extends RefCounted
class_name OnlinePerformance

const SUMMARY_INTERVAL_MS := 1_000
const SAMPLE_LIMIT := 120
const WAIT_REASONS := ["clock", "input", "control", "confirmation", "paused", "recovery"]
const WORK_KINDS := ["coordinator_tick", "tick_interval", "simulation_step", "input_receive", "correction"]
const CHECKPOINT_COUNTERS := ["saves", "encodeUs", "packUs", "retainsUs"]

var active := false
var _match_started_ms := -1
var _window_started_ms := -1
var _window_frontier := 0
var _window_confirmed := 0
var _match_frontier := 0
var _last_summary_ms := -1
var _last_tick_started_usec := -1
var _open_tick_started_usec := -1
var _open_tick_frontier := 0
var _current_wait := ""
var _wait_accounted_until_ms := -1
var _page_visible := true
var _hidden_accounted_until_ms := -1
var _window_work: Dictionary = {}
var _match_work: Dictionary = {}
var _window_wait_ms: Dictionary = {}
var _match_wait_ms: Dictionary = {}
var _window_wait_count: Dictionary = {}
var _match_wait_count: Dictionary = {}
var _window_frontier_advanced := 0
var _match_frontier_advanced := 0
var _window_hidden_ms := 0
var _match_hidden_ms := 0
var _window_hidden_count := 0
var _match_hidden_count := 0
var _checkpoint_previous: Dictionary = {}


func start(now_ms: int, frontier: int, confirmed: int, page_visible: bool, checkpoint_profile: Dictionary) -> void:
	active = true
	_match_started_ms = now_ms
	_window_started_ms = now_ms
	_last_summary_ms = now_ms
	_match_frontier = frontier
	_window_frontier = frontier
	_window_confirmed = confirmed
	_last_tick_started_usec = -1
	_open_tick_started_usec = -1
	_current_wait = ""
	_wait_accounted_until_ms = now_ms
	_page_visible = page_visible
	_hidden_accounted_until_ms = now_ms if not page_visible else -1
	_window_frontier_advanced = 0
	_match_frontier_advanced = 0
	_window_hidden_ms = 0
	_match_hidden_ms = 0
	_window_hidden_count = 0
	_match_hidden_count = 0
	_window_wait_ms = _empty_wait_values()
	_match_wait_ms = _empty_wait_values()
	_window_wait_count = _empty_wait_values()
	_match_wait_count = _empty_wait_values()
	_window_work = _empty_work_values(true)
	_match_work = _empty_work_values(false)
	_checkpoint_previous = _normalized_checkpoint_totals(checkpoint_profile)


func begin_tick(now_usec: int, frontier: int) -> void:
	if not active:
		return
	if _last_tick_started_usec >= 0:
		_record_work("tick_interval", now_usec - _last_tick_started_usec)
	_last_tick_started_usec = now_usec
	_open_tick_started_usec = now_usec
	_open_tick_frontier = frontier


func finish_tick(now_usec: int, frontier: int) -> void:
	if not active or _open_tick_started_usec < 0:
		return
	_record_work("coordinator_tick", now_usec - _open_tick_started_usec)
	if frontier > _open_tick_frontier:
		var advanced := frontier - _open_tick_frontier
		_window_frontier_advanced += advanced
		_match_frontier_advanced += advanced
	_open_tick_started_usec = -1


func record_simulation_step(elapsed_usec: int) -> void:
	_record_work("simulation_step", elapsed_usec)


func record_input_receive(elapsed_usec: int, correction_count: int, replayed_frames: int) -> void:
	if not active:
		return
	_record_work("input_receive", elapsed_usec)
	if correction_count <= 0:
		return
	_record_work("correction", elapsed_usec)
	_window_work.correctionCount += correction_count
	_match_work.correctionCount += correction_count
	_window_work.replayedFrames += maxi(0, replayed_frames)
	_match_work.replayedFrames += maxi(0, replayed_frames)


func set_wait(reason: String, now_ms: int) -> void:
	if not active:
		return
	var next_reason := reason if reason in WAIT_REASONS else ""
	if next_reason == _current_wait:
		return
	_account_wait(now_ms)
	_current_wait = next_reason
	_wait_accounted_until_ms = now_ms
	if not next_reason.is_empty():
		_window_wait_count[next_reason] += 1
		_match_wait_count[next_reason] += 1


func set_page_visible(visible: bool, now_ms: int) -> void:
	if not active:
		return
	if visible == _page_visible:
		return
	_account_hidden(now_ms)
	_page_visible = visible
	_hidden_accounted_until_ms = now_ms if not visible else -1
	if not visible:
		_window_hidden_count += 1
		_match_hidden_count += 1


func summary_due(now_ms: int) -> bool:
	return active and _last_summary_ms >= 0 and now_ms - _last_summary_ms >= SUMMARY_INTERVAL_MS


func collect_summary(now_ms: int, now_usec: int, frontier: int, confirmed: int,
		context: Dictionary, checkpoint_profile: Dictionary, final: bool = false) -> Dictionary:
	if not active:
		return {"schemaVersion": 1, "available": false, "reason": "match_not_started"}
	finish_tick(now_usec, frontier)
	_account_wait(now_ms)
	_account_hidden(now_ms)
	var elapsed_ms := maxi(0, now_ms - _window_started_ms)
	var match_elapsed_ms := maxi(0, now_ms - _match_started_ms)
	var frontier_delta := frontier - _window_frontier
	var match_frontier_delta := frontier - _match_frontier
	var confirmed_delta := confirmed - _window_confirmed
	var summary := {
		"schemaVersion": 1,
		"available": true,
		"final": final,
		"windowMs": elapsed_ms,
		"matchElapsedMs": match_elapsed_ms,
		"frontier": frontier,
		"confirmed": confirmed,
		"frontierDelta": frontier_delta,
		"frontierAdvanced": _window_frontier_advanced,
		"frontierHz": _rate(frontier_delta, elapsed_ms),
		"matchFrontierDelta": match_frontier_delta,
		"matchFrontierAdvanced": _match_frontier_advanced,
		"matchFrontierHz": _rate(match_frontier_delta, match_elapsed_ms),
		"confirmedDelta": confirmed_delta,
		"tickCount": int(_window_work.coordinator_tick.count),
		"coordinatorTickTotalUs": int(_window_work.coordinator_tick.totalUs),
		"coordinatorTickMaxUs": int(_window_work.coordinator_tick.maxUs),
		"coordinatorTickP95Us": _percentile("coordinator_tick", 0.95),
		"coordinatorTickP99Us": _percentile("coordinator_tick", 0.99),
		"coordinatorTickSampleCount": int(_window_work.coordinator_tick.samples.size()),
		"coordinatorTickSampleDropped": int(_window_work.coordinator_tick.sampleDropped),
		"coordinatorTickSamplesTruncated": int(_window_work.coordinator_tick.sampleDropped) > 0,
		"simulationStepCount": int(_window_work.simulation_step.count),
		"simulationStepTotalUs": int(_window_work.simulation_step.totalUs),
		"simulationStepMaxUs": int(_window_work.simulation_step.maxUs),
		"simulationStepP95Us": _percentile("simulation_step", 0.95),
		"simulationStepP99Us": _percentile("simulation_step", 0.99),
		"simulationStepSampleCount": int(_window_work.simulation_step.samples.size()),
		"simulationStepSampleDropped": int(_window_work.simulation_step.sampleDropped),
		"simulationStepSamplesTruncated": int(_window_work.simulation_step.sampleDropped) > 0,
		"tickIntervalCount": int(_window_work.tick_interval.count),
		"tickIntervalMaxUs": int(_window_work.tick_interval.maxUs),
		"tickIntervalP95Us": _percentile("tick_interval", 0.95),
		"tickIntervalP99Us": _percentile("tick_interval", 0.99),
		"tickIntervalSampleCount": int(_window_work.tick_interval.samples.size()),
		"tickIntervalSampleDropped": int(_window_work.tick_interval.sampleDropped),
		"tickIntervalSamplesTruncated": int(_window_work.tick_interval.sampleDropped) > 0,
		"inputReceiveCount": int(_window_work.input_receive.count),
		"inputReceiveTotalUs": int(_window_work.input_receive.totalUs),
		"inputReceiveMaxUs": int(_window_work.input_receive.maxUs),
		"inputReceiveP95Us": _percentile("input_receive", 0.95),
		"inputReceiveP99Us": _percentile("input_receive", 0.99),
		"inputReceiveSampleCount": int(_window_work.input_receive.samples.size()),
		"inputReceiveSampleDropped": int(_window_work.input_receive.sampleDropped),
		"inputReceiveSamplesTruncated": int(_window_work.input_receive.sampleDropped) > 0,
		"correctionCount": int(_window_work.correctionCount),
		"replayedFrames": int(_window_work.replayedFrames),
		"correctionReceiveTotalUs": int(_window_work.correction.totalUs),
		"correctionReceiveMaxUs": int(_window_work.correction.maxUs),
		"correctionReceiveP95Us": _percentile("correction", 0.95),
		"correctionReceiveP99Us": _percentile("correction", 0.99),
		"correctionReceiveSampleCount": int(_window_work.correction.samples.size()),
		"correctionReceiveSampleDropped": int(_window_work.correction.sampleDropped),
		"correctionReceiveSamplesTruncated": int(_window_work.correction.sampleDropped) > 0,
		"correctionReceiveTimingScope": "full rollback.receive() call when rollback_count increases, including non-replay receive overhead",
		"waitMs": _window_wait_ms.duplicate(true),
		"waitCount": _window_wait_count.duplicate(true),
		"pageVisible": _page_visible,
		"hiddenMs": _window_hidden_ms,
		"hiddenCount": _window_hidden_count,
		"recovering": bool(context.get("recovering", false)),
		"paused": bool(context.get("paused", false)),
		"currentWait": _current_wait,
		"checkpoint": _checkpoint_summary(checkpoint_profile),
		"network": {"rttAvailable": false, "rttMs": null,
			"rttReason": "peer_transport_does_not_expose_reliable_rtt_stats"},
		"profile": context.get("profile", {}).duplicate(true) if context.get("profile", {}) is Dictionary else {},
		"matchTotals": _match_totals(),
	}
	_window_started_ms = now_ms
	_window_frontier = frontier
	_window_confirmed = confirmed
	_window_frontier_advanced = 0
	_window_hidden_ms = 0
	_window_hidden_count = 0
	_window_wait_ms = _empty_wait_values()
	_window_wait_count = _empty_wait_values()
	_window_work = _empty_work_values(true)
	_last_summary_ms = now_ms
	if final:
		active = false
	return summary


func stop() -> void:
	active = false
	_open_tick_started_usec = -1
	for kind in WORK_KINDS:
		if _window_work.has(kind):
			_window_work[kind].samples.clear()


func _record_work(kind: String, elapsed_usec: int) -> void:
	if not active or kind not in WORK_KINDS:
		return
	var duration := maxi(0, elapsed_usec)
	var window_stat: Dictionary = _window_work[kind]
	window_stat.count += 1
	window_stat.totalUs += duration
	window_stat.maxUs = maxi(int(window_stat.maxUs), duration)
	if window_stat.samples.size() < SAMPLE_LIMIT:
		window_stat.samples.append(duration)
	else:
		window_stat.samples[int(window_stat.sampleCursor)] = duration
		window_stat.sampleCursor = (int(window_stat.sampleCursor) + 1) % SAMPLE_LIMIT
		window_stat.sampleDropped += 1
	var match_stat: Dictionary = _match_work[kind]
	match_stat.count += 1
	match_stat.totalUs += duration
	match_stat.maxUs = maxi(int(match_stat.maxUs), duration)


func _percentile(kind: String, fraction: float) -> int:
	var samples: Array = _window_work[kind].samples.duplicate()
	if samples.is_empty():
		return -1
	samples.sort()
	var index := clampi(int(ceil(float(samples.size()) * fraction)) - 1, 0, samples.size() - 1)
	return int(samples[index])


func _account_wait(now_ms: int) -> void:
	if _current_wait.is_empty() or _wait_accounted_until_ms < 0:
		return
	var elapsed := maxi(0, now_ms - _wait_accounted_until_ms)
	_window_wait_ms[_current_wait] += elapsed
	_match_wait_ms[_current_wait] += elapsed
	_wait_accounted_until_ms = now_ms


func _account_hidden(now_ms: int) -> void:
	if _page_visible or _hidden_accounted_until_ms < 0:
		return
	var elapsed := maxi(0, now_ms - _hidden_accounted_until_ms)
	_window_hidden_ms += elapsed
	_match_hidden_ms += elapsed
	_hidden_accounted_until_ms = now_ms


func _checkpoint_summary(checkpoint_profile: Dictionary) -> Dictionary:
	if not bool(checkpoint_profile.get("available", false)):
		return {"available": false, "reason": str(checkpoint_profile.get("reason", "checkpoint_profile_unavailable"))}
	var totals: Dictionary = _normalized_checkpoint_totals(checkpoint_profile)
	var delta := {}
	for key in CHECKPOINT_COUNTERS:
		delta[key] = int(totals[key]) - int(_checkpoint_previous.get(key, totals[key]))
	_checkpoint_previous = totals.duplicate(true)
	return {"available": true, "totals": totals, "windowDelta": delta}


func _normalized_checkpoint_totals(value: Dictionary) -> Dictionary:
	if not bool(value.get("available", false)):
		return {}
	var totals: Dictionary = value.get("totals", {}) if value.get("totals") is Dictionary else value
	var normalized := {}
	for key in CHECKPOINT_COUNTERS:
		var counter: Variant = totals.get(key)
		normalized[key] = int(counter) if counter is int or counter is float else 0
	return normalized


func _match_totals() -> Dictionary:
	var work := {}
	for kind in WORK_KINDS:
		var stat: Dictionary = _match_work[kind]
		work[kind] = {"count": int(stat.count), "totalUs": int(stat.totalUs), "maxUs": int(stat.maxUs)}
	return {
		"work": work,
		"correctionCount": int(_match_work.correctionCount),
		"replayedFrames": int(_match_work.replayedFrames),
		"frontierAdvanced": _match_frontier_advanced,
		"waitMs": _match_wait_ms.duplicate(true),
		"waitCount": _match_wait_count.duplicate(true),
		"hiddenMs": _match_hidden_ms,
		"hiddenCount": _match_hidden_count,
	}


func _empty_work_values(with_samples: bool) -> Dictionary:
	var result := {"correctionCount": 0, "replayedFrames": 0}
	for kind in WORK_KINDS:
		var stat := {"count": 0, "totalUs": 0, "maxUs": 0}
		if with_samples:
			stat["samples"] = []
			stat["sampleCursor"] = 0
			stat["sampleDropped"] = 0
		result[kind] = stat
	return result


func _empty_wait_values() -> Dictionary:
	var result := {}
	for reason in WAIT_REASONS:
		result[reason] = 0
	return result


func _rate(frames: int, elapsed_ms: int) -> Variant:
	return float(frames) * 1000.0 / float(elapsed_ms) if elapsed_ms > 0 else null
