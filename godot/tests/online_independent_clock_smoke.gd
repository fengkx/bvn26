extends SceneTree
const Fixture = preload("res://tests/rollback_fixture.gd")
const Coordinator = preload("res://online_match.gd")
const Timers = preload("res://online_timer_authority.gd")
const State = preload("res://simulation_state.gd")
const Session = preload("res://rollback_session.gd")
func _initialize() -> void:
	_run.call_deferred()
func _run() -> void:
	var fixtures := [Fixture.create(self), Fixture.create(self)]
	var peers := []
	for index in 2:
		var peer := Coordinator.new()
		peer.game = fixtures[index].game
		peer.battle = fixtures[index].battle
		peer.timers = Timers.new()
		peer.local_slot = "p1" if index == 0 else "p2"
		assert(peer.timers.configure(peer.game, 0).is_empty())
		assert(peer.battle.set_event_supplier(Callable(peer.timers, "events_for_phase")).is_empty())
		peers.append(peer)
	print("ONLINE_CHECKPOINT_BYTES initial=%d" % var_to_bytes(peers[0].save_state()).size())
	var held := {}
	for button in Session.BUTTONS: held[button] = false
	var checkpoint := {}
	for frame in range(1, 61):
		for index in 2:
			peers[index]._process_now_ms = frame * (33 if index == 0 else 999)
			assert(peers[index].advance(frame, {"p1": held, "p2": held}).is_empty())
		if frame == 30: checkpoint = peers[1].save_state()
	assert(State.first_difference(peers[0].save_state(), peers[1].save_state()).is_empty())
	var final: Dictionary = peers[1].save_state()
	print("ONLINE_CHECKPOINT_BYTES frame60=%d" % var_to_bytes(final).size())
	peers[1].begin_replay()
	assert(peers[1].load_state(checkpoint).is_empty())
	for frame in range(31, 61):
		assert(peers[1].advance(frame, {"p1": held, "p2": held}).is_empty())
	peers[1].end_replay()
	assert(State.first_difference(final, peers[1].save_state()).is_empty())
	for fixture in fixtures: Fixture.dispose(fixture.game, fixture.battle)
	print("ONLINE_INDEPENDENT_CLOCK_SMOKE_OK no_packets=true skewed_wall_clock=true replay_equal=true")
	quit()
