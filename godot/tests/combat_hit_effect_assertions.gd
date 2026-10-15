extends RefCounted


static func run(tree: SceneTree) -> void:
	var hit_effect_script = load("res://hit_effect_runtime.gd")
	var hit_effect: HitEffectRuntime = hit_effect_script.new()
	hit_effect.auto_advance = false
	hit_effect.configure("XG_qdjx", Vector2(200.0, -25.0), 1)
	tree.root.add_child(hit_effect)
	await tree.process_frame
	# Preview plus the frame-1 StartSound player (soundId 219).
	assert(hit_effect.get_child_count() == 2)
	var effect_preview := hit_effect.get_child(0) as TimelinePreview
	assert(effect_preview.current_source_frame() in [1, 2])
	assert(effect_preview.get_child_count() > 0)
	assert(hit_effect.last_sound_ids == [219])
	assert((hit_effect.get_child(1) as AudioStreamPlayer).playing)
	assert(hit_effect.effect_frame == 1)
	assert(not hit_effect.game_paused)
	hit_effect.advance_effect()
	assert(hit_effect.effect_frame == 2)
	assert(hit_effect.game_paused)
	assert("pause_game" in hit_effect.last_ops)
	assert("shine" in hit_effect.last_ops)
	while hit_effect.effect_frame < 15:
		hit_effect.advance_effect()
	assert(not hit_effect.game_paused)
	assert("resume_game" in hit_effect.last_ops)
	hit_effect.auto_advance = true
	for _tick in range(20):
		await tree.physics_frame
	assert(not is_instance_valid(hit_effect))

	var finisher_effect: HitEffectRuntime = hit_effect_script.new()
	finisher_effect.configure("XG_mfdjx", Vector2(200.0, -25.0), 1)
	tree.root.add_child(finisher_effect)
	await tree.process_frame
	var finisher_preview := finisher_effect.get_child(0) as TimelinePreview
	assert(finisher_preview.get_child_count() > 0)
	for _tick in range(18):
		await tree.physics_frame
	assert(not is_instance_valid(finisher_effect))

	# Source XG_fykan: frame 1 StartSound 215 with no envelope, frame 11
	# this.unloadMovie(). Blocked 斩 must be seen and heard.
	var guard_effect: HitEffectRuntime = hit_effect_script.new()
	guard_effect.auto_advance = false
	guard_effect.configure("XG_fykan", Vector2(200.0, -25.0), 1)
	tree.root.add_child(guard_effect)
	await tree.process_frame
	var guard_preview := guard_effect.get_child(0) as TimelinePreview
	assert(guard_preview.get_child_count() > 0)
	assert(guard_effect.last_sound_ids == [215])
	var guard_player := guard_effect.get_child(1) as AudioStreamPlayer
	assert(guard_player.playing)
	assert(is_equal_approx(guard_player.volume_db, 0.0))
	while guard_effect.effect_frame < 11:
		guard_effect.advance_effect()
	assert("unload" in guard_effect.last_ops)
	await tree.process_frame
	assert(not is_instance_valid(guard_effect))

	# XG_fyq carries a source SOUNDINFO envelope; the generated sound segment is
	# envelope_baked, so the player uses the baked stream at neutral gain.
	var ring_effect: HitEffectRuntime = hit_effect_script.new()
	ring_effect.auto_advance = false
	ring_effect.configure("XG_fyq", Vector2(200.0, -25.0), 1)
	tree.root.add_child(ring_effect)
	await tree.process_frame
	assert(ring_effect.last_sound_ids == [197])
	var ring_player := ring_effect.get_child(1) as AudioStreamPlayer
	assert(ring_player.playing)
	assert(is_equal_approx(ring_player.volume_db, 0.0))
	ring_effect.queue_free()
	await tree.process_frame
