extends SceneTree


func _initialize() -> void:
	var director := SuperRuntime.new()
	var helper := HelperRuntime.new()
	helper.attacking = true
	# Helper frame 1 never defines sw; main stopMc/playMc require sw === false.
	helper.timeline_playing = true
	director.stop_mc(helper)
	if not helper.timeline_playing:
		push_error("stopMc froze a helper whose source sw is undefined")
		helper.free()
		quit(1)
		return
	helper.timeline_playing = false
	director.play_mc(helper)
	assert(not helper.timeline_playing)
	# An explicitly false field must still pass the source strict comparison.
	helper.sw = false
	helper.timeline_playing = true
	director.stop_mc(helper)
	assert(not helper.timeline_playing)
	director.play_mc(helper)
	assert(helper.timeline_playing)
	helper.free()
	print("HELPER_PAUSE_SEMANTICS_OK")
	quit()
