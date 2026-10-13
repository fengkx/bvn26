extends "res://tests/move_case_reference.gd"

# Replay observed wall-clock callbacks without shifting source state rows.
var next_observed_tick := 0
var fired_ticks: Array[int] = []


func _run_case(fixture_path: String, output_path: String) -> void:
	next_observed_tick = 0
	fired_ticks.clear()
	await super._run_case(fixture_path, output_path)
	assert(fired_ticks.size() == fixture.get("recorded_nextfight", []).size())


func _observe(tick: int) -> void:
	super._observe(tick)
	next_observed_tick = tick + 1


func _drive_source_timers(delta_ms: float) -> void:
	if not fixture.has("recorded_nextfight"):
		super._drive_source_timers(delta_ms)
		return
	assert(not str(fixture.get("timer_input_provenance", {}).get("source_trace_sha256", "")).is_empty())
	if game == null:
		return
	if game.ko_nextfight_timer != null:
		game.ko_nextfight_timer.paused = true
	for event: Dictionary in fixture.recorded_nextfight:
		var delivery_tick := int(event.delivery_tick)
		if delivery_tick != next_observed_tick or fired_ticks.has(delivery_tick):
			continue
		assert(game.ko_nextfight_timer != null, "Recorded callback has no registered source interval")
		game.ko_nextfight_timer.timeout.emit()
		fired_ticks.append(delivery_tick)
