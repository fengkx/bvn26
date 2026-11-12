extends RefCounted


# Stopping players schedules mixer-side deletion followed by main-thread cleanup.
# Call only after freeing the scene; this does not advance the replay itself.
static func drain(tree: SceneTree, timeout_ms: int = 2000) -> bool:
	var deadline := Time.get_ticks_msec() + timeout_ms
	var last_mix := _last_mix_usec()
	var completed_mixes := 0
	while completed_mixes < 2:
		await tree.process_frame
		var current_mix := _last_mix_usec()
		# The two API reads have microsecond skew. A millisecond separates real
		# mixer epochs without mistaking that measurement skew for a mix.
		if current_mix > last_mix + 1000:
			completed_mixes += 1
			last_mix = current_mix
		if Time.get_ticks_msec() >= deadline:
			push_error("Audio shutdown timed out waiting for mixer retirement")
			return false
	# AudioServer.update drains retired entries on the main thread.
	await tree.process_frame
	await tree.process_frame
	return true


static func _last_mix_usec() -> int:
	return Time.get_ticks_usec() - int(AudioServer.get_time_since_last_mix() * 1000000.0)
