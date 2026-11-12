extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	# Exercise the real filter compiler, including its built-in TEXTURE samples.
	var material := ShaderMaterial.new()
	material.shader = load("res://flash_filter.gdshader")
	assert(not material.shader.get_shader_uniform_list().is_empty())
	material = null
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = 44100
	var samples := PackedByteArray()
	samples.resize(88200)
	stream.data = samples
	var player := AudioStreamPlayer.new()
	root.add_child(player)
	player.stream = stream
	player.play()
	var playback_ref: WeakRef = weakref(player.get_stream_playback())
	var stream_ref: WeakRef = weakref(stream)
	assert(playback_ref.get_ref() != null)
	stream = null
	player.queue_free()
	await process_frame
	assert(await preload("res://tests/audio_shutdown.gd").drain(self))
	assert(playback_ref.get_ref() == null, "Playback must be retired before exit")
	assert(stream_ref.get_ref() == null, "Stream must be released before exit")
	print("REPLAY_SHUTDOWN_OK shader_compiled playback_released stream_released")
	quit()
