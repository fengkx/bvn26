extends SceneTree
func _initialize() -> void:
	_run.call_deferred()
func _run() -> void:
	var lobby := OnlineLobby.new()
	root.add_child(lobby)
	lobby._room_state = {"phase": "lobby", "match": null}
	lobby._slot = 0
	assert(lobby._apply_network_url_options("0", "3"))
	assert(lobby._current_network_profile() == {"id": "chrome-exp-d3-p0", "inputDelay": 3, "predictionWindow": 0})
	assert(not lobby._apply_network_url_options("bad", "7"))
	assert(lobby._apply_network_url_options("0", "4"))
	lobby._slot = 1
	assert(not lobby._apply_network_url_options("0", "3"))
	assert(lobby._current_network_profile().inputDelay == 4)
	lobby._slot = 0
	lobby._room_state.phase = "active"
	assert(not lobby._apply_network_url_options("0", "3"))
	var generation: int = lobby._lifecycle_generation
	await lobby._start_prepared_match({"phase": "preparing", "match": {"epoch": "old"}})
	assert(lobby._lifecycle_generation == generation and lobby.coordinator == null)
	lobby._room_state = {"phase": "preparing", "match": {"epoch": "new"}}
	await lobby._start_prepared_match({"phase": "preparing", "match": {"epoch": "old"}})
	assert(lobby._lifecycle_generation == generation and lobby._starting_epoch.is_empty())
	lobby.free()
	print("ONLINE_PROFILE_EPOCH_SMOKE_OK host_negotiation_only=true frozen_active=true stale_deferred_start_ignored=true")
	quit()
