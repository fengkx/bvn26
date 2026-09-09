extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var state := AiSourceState.new()
	var model: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/fighters/yihu/ai.json"))
	state.configure(model)
	var random := SourceRandom.new()
	var clock := AiRandomClock.new()
	root.add_child(clock)
	var sound := StageSound.new()
	sound.random_source = random
	root.add_child(sound)
	await process_frame
	var fields: Array = model["random_refresh"]["assignments"]
	assert(int(model["random_refresh"]["interval_ms"]) == 500)
	assert(fields.map(func(x: Dictionary) -> String: return x["field"]) == ["attran", "defran", "goran", "jumpran", "bisharan"])
	var tape: Array = [{"site": "main#DefineSprite_1900/frame_1/DoAction.as:1", "value": 0.5}]
	var raw := [0.0, 0.25, 0.5, 0.75, 0.875]
	for i in fields.size():
		tape.append({"site": fields[i]["site"], "value": raw[i]})
	assert(random.use_recorded_tape(tape))
	assert(sound.select() == "ichigo.mp3")
	clock.initialize(state, random, 5, true)
	assert(random.consumed.size() == 1)
	assert(state.read_field("attran") == null)
	assert(clock.sample_count == 0)
	assert(clock.fire_recorded(11863))
	assert(random.replay_complete())
	var easy := [0.0, 125.0, 250.0, 375.0, 437.5]
	for i in fields.size():
		assert(state.read_field(fields[i]["field"]) == easy[i])
	state.apply_frame(1)
	assert(state.read_field("goran") == 250.0)
	clock.cancel()
	# All five source levels use the same assignments, changing only 100*AI.
	for level in range(1, 6):
		assert(random.use_recorded_tape(tape.slice(1)))
		clock.initialize(state, random, level, true)
		assert(clock.fire_recorded(500))
		for i in fields.size():
			assert(state.read_field(fields[i]["field"]) == raw[i] * 100 * level)
		clock.cancel()
	# Both exhaustion and reordered consumers fail without consuming a fallback.
	assert(random.use_recorded_tape([]))
	assert(is_nan(random.next_value("unexpected")))
	assert(random.failure.contains("exhausted"))
	assert(random.consumed.is_empty())
	assert(random.use_recorded_tape(tape))
	assert(is_nan(random.next_value(fields[0]["site"])))
	assert(random.failure.contains("mismatch"))
	assert(random.consumed.is_empty())
	assert(not random.use_recorded_tape([{"site": "bad", "value": "0.5"}]))
	# A real elapsed-time timer keeps running while scene playback is paused
	# and Engine.time_scale is reduced. Recorded event delivery is tested above.
	random.use_live_random()
	clock.initialize(state, random, 5)
	assert(clock.sample_count == 0)
	paused = true
	Engine.time_scale = 0.01
	await create_timer(0.65, true, false, true).timeout
	Engine.time_scale = 1.0
	paused = false
	assert(clock.sample_count >= 1)
	assert(random.consumed.size() == clock.sample_count * 5)
	for assignment: Dictionary in fields:
		var v := float(state.read_field(assignment["field"]))
		assert(v >= 0.0 and v < 500.0)
	clock.cancel()
	var count := clock.sample_count
	await create_timer(0.55, true, false, true).timeout
	assert(clock.sample_count == count)
	clock.queue_free()
	sound.queue_free()
	await process_frame
	print("AI_RANDOM_SMOKE_OK")
	quit()
