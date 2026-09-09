extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var random := SourceRandom.new()
	var sites := "main#DefineSprite_256_XG_qdj/frame_1/DoAction.as:"
	var tape: Array = []
	for i in 8:
		tape.append({"index": i + 1, "site": sites + str(i % 4 + 1), "value": 0.25})
	assert(random.use_recorded_tape(tape))
	var effects: Array[HitEffectRuntime] = []
	for i in 2:
		var effect := HitEffectRuntime.new()
		effect.auto_advance = false
		effect.defer_initial_frame = true
		effect.source_random = random
		root.add_child(effect)
		effect.configure("XG_qdj", Vector2(100, 200), -1, 0)
		effects.append(effect)
	assert(random.consumed.is_empty())
	for i in 2:
		var effect := effects[i]
		effect.run_initial_frame()
		assert(random.consumed.size() == (i + 1) * 4)
		# _X/_Y are parent coordinates; mirroring the sprite must not flip the offset.
		assert(effect.position == Vector2(100, 197.5))
		effect.run_initial_frame()
		assert(random.consumed.size() == (i + 1) * 4)
		for frame in range(2, 19):
			effect.advance_effect()
			assert(not effect.is_queued_for_deletion())
		effect.advance_effect()
		assert(effect.effect_frame == 19 and effect.is_queued_for_deletion())
	assert(random.replay_complete())
	await process_frame
	print("HIT_EFFECT_RANDOM_SMOKE_OK")
	quit()
