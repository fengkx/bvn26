extends SceneTree

# Locks the compiled loadSound() pick order and startGame() playback numbers.
# Source: DefineSprite_1900/frame_1 loadSound(), frame_8 startGame().


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var script = load("res://stage_sound.gd")
	var stage_sound: StageSound = script.new()
	root.add_child(stage_sound)
	await process_frame
	assert(stage_sound.load_manifest())

	# Step 1 is the p2selt catalog music, drawn against Math.random() < 0.8.
	stage_sound.random_tape = [0.5]
	assert(stage_sound.select() == "ichigo.mp3")
	assert(stage_sound.selected_source == "fighter_catalog.一护.music")
	assert(stage_sound.draws == [0.5])

	# Failing step 1 draws a second random; < 0.5 takes bleachMusic because
	# 一护 has no isNaruto flag.
	stage_sound.random_tape = [0.85, 0.2]
	assert(stage_sound.select() == "bleach.mp3")
	assert(stage_sound.selected_source == "bleachMusic")
	assert(stage_sound.draws == [0.85, 0.2])

	# Otherwise getMapData(curStage).music, with no third draw.
	stage_sound.random_tape = [0.85, 0.7]
	assert(stage_sound.select() == "city.mp3")
	assert(stage_sound.selected_source == "map_catalog.现世.music")
	assert(stage_sound.draws.size() == 2)

	# Source uses `<`, so the threshold value itself falls through.
	stage_sound.random_tape = [0.8, 0.5]
	assert(stage_sound.select() == "city.mp3")

	# startGame(): start(0,999) then setVolume(80).
	assert(is_equal_approx(stage_sound.volume_db(), linear_to_db(0.8)))
	stage_sound.random_tape = [0.5]
	stage_sound.select()
	stage_sound.start()
	await process_frame
	assert(stage_sound.playing())
	var stream: AudioStream = stage_sound._player.stream
	assert(stream is AudioStreamMP3)
	assert(stream.loop)
	assert(is_equal_approx(stage_sound._player.volume_db, linear_to_db(0.8)))
	stage_sound.stop()
	assert(not stage_sound.playing())

	stage_sound.queue_free()
	await process_frame
	print("stage_sound_smoke ok")
	quit()
