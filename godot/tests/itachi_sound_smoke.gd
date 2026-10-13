extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var preview := TimelinePreview.new()
	preview.fighter_directory = "res://generated/fighters/itachi"
	root.add_child(preview)
	var event: Dictionary = preview._nested_sound_segments["61:10"][0].source_event
	assert(event.sound_id == 42)
	assert(preview._play_nested_source_sound(event, "source-61", 61, 10))
	assert(preview.last_nested_sound_ids == [42])
	var players := preview.find_children("*", "AudioStreamPlayer", true, false)
	assert(players.size() == 1)
	var player: AudioStreamPlayer = players[0]
	assert(player.stream is AudioStreamWAV)
	assert(player.volume_db == 0, "The baked per-channel envelope must not be attenuated twice")
	player.stop()
	player.stream = null
	preview.queue_free()
	await process_frame
	print("ITACHI_SOUND_SMOKE_OK sprite=61 frame=10 sound=42 envelope=baked")
	quit()
