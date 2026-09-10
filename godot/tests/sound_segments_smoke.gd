extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var preview := TimelinePreview.new()
	preview.fighter_directory = "res://generated/fighters/rifagu"
	preview.autoplay = false
	root.add_child(preview)
	preview.play_source_frame(253)
	assert(preview.last_sound_ids == [150])
	var players := preview._sound_layer().get_children()
	var sound: AudioStreamPlayer = players.back()
	assert(sound.stream is AudioStreamWAV)
	assert(is_equal_approx(sound.stream.get_length(), 32464.0 / 44100.0))
	assert(sound.volume_db == 0.0)
	preview.refresh_display()
	assert(preview._sound_layer().get_child_count() == players.size())
	preview.queue_free()
	await process_frame
	# XG_bs has an authored out point beyond the decoded sound's natural end.
	var sample_counts := {"XG_bs": 45588, "XG_fzcc": 17950, "XG_fzbs": 25000}
	for clip: String in sample_counts:
		var effect := HitEffectRuntime.new()
		effect.auto_advance = false
		effect.defer_initial_frame = true
		effect.configure(clip, Vector2.ZERO, 1)
		root.add_child(effect)
		assert(effect.find_children("*", "AudioStreamPlayer", true, false).is_empty())
		effect.run_initial_frame()
		var effect_sounds := effect.find_children("*", "AudioStreamPlayer", true, false)
		assert(effect_sounds.size() == 1)
		var effect_sound: AudioStreamPlayer = effect_sounds[0]
		assert(effect_sound.stream is AudioStreamWAV)
		assert(is_equal_approx(effect_sound.stream.get_length(), float(sample_counts[clip]) / 44100.0))
		effect.queue_free()
		await process_frame
	print("SOUND_SEGMENTS_SMOKE_OK")
	quit()
