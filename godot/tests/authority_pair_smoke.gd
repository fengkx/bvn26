extends "res://tests/rollback_delayed_input_profile.gd"

const Pair = preload("res://tests/online_pair_fixture.gd")
const Authority = preload("res://authority_match.gd")
const Wire = preload("res://authority_wire.gd")

class Coordinator extends Authority:
	var cost := 100
	func _run_probe() -> Dictionary:
		return {"profile": HostSelection.PROFILE, "samples": 120, "visible": true, "p95_us": cost, "long_stalls": 0}

class Hub extends Pair.FakeHub:
	var wire := Wire.new()
	var display_ready := false
	var block_state_acks := false
	var initial_send_times: Array[int] = []
	func command(slot: int, operation: Dictionary) -> Dictionary:
		if operation.type == "authority_ack":
			state.match.authoritySlot = operation.authoritySlot
			return {"acceptedSeq": 1, "state": state.duplicate(true)}
		var result := super.command(slot, operation)
		if state.phase == "lobby" and state.lastResult is Dictionary and state.lastResult.reason == "agreed":
			state.lastResult.reason = "host-declared/guest-received"
			state.lastResult.mode = "host-authoritative"
			state.lastResult.authoritySlot = authority
			result.state = state.duplicate(true)
		return result
	var authority := 0
	func send_peer(slot: int, channel: String, type: String, payload: Dictionary) -> void:
		if not peers.has(1 - slot): return
		if type == "authority_state_ack" and block_state_acks: return
		if type == "authority_display_ready": display_ready = true
		if channel == "state" and payload.get("initial", false):
			assert(display_ready, "Initial state preceded presenter readiness")
			initial_send_times.append(Time.get_ticks_msec())
			if initial_send_times.size() == 1: return # Exercise unreliable initial-state loss.
			assert(initial_send_times[-1] - initial_send_times[-2] >= Authority.INITIAL_STATE_RETRY_MS)
		var value: Dictionary
		if channel == "state":
			var bytes := wire.encode(payload)
			assert(not bytes.is_empty(), wire.error)
			value = wire.decode(bytes)
		else: value = _json_numbers_as_floats(JSON.parse_string(JSON.stringify(payload)))
		var peer: Object = peers[1 - slot]
		next_peer_sequence[slot] += 1
		peer.peer_message.emit(channel, type, value, next_peer_sequence[slot])
		peer.message_drain_completed.emit(1)

class Transport extends Pair.FakeTransport:
	var enable_state_channel := false
	func get_channel_state(_channel: String) -> String:
		return "open" if peer_created and link_connected and hub.peers.size() == 2 else "closed"
	func send_peer_message(channel: String, type: String, payload: Dictionary) -> bool:
		if not peer_created or not link_connected: return false
		hub.send_peer(slot, channel, type, payload)
		return true

var starts := {}
var scenes := {}

func _scene(role: String, slot: int) -> Dictionary:
	if scenes.has(slot):
		if not scenes[slot].presentation_only: scenes[slot]._goto_menu()
		scenes[slot].free()
	var game: Node = load("res://main.tscn").instantiate()
	if role == "guest":
		game.prepare_presentation_only()
		root.add_child(game)
	else:
		root.add_child(game)
		game.set_physics_process(false)
		game.set_process(false)
		game.ko_recorded_timers = true
		game.recorded_training_timers = true
		game.source_random.use_seed(727)
		game.source_clock.use_explicit_time(0)
		game._replace_selected_actors(["鸣人", "一护"], ["我爱罗", "魂"])
		game._load_selected_stage("现世")
		game._enter_current_fight(3)
		game.battle_intro.recorded_polling = true
		for timer in game.title_menu.find_children("*", "Timer", true, false): timer.stop()
	scenes[slot] = game
	return {"game": game}

func _start(coordinator: Coordinator, epoch: String, profile: Dictionary, slot: int) -> void:
	starts[slot] = await coordinator.start(epoch, profile)

func _run() -> void:
	for host_slot in [0, 1]:
		starts.clear()
		var setup := {"mode": "host-authoritative", "members": [{"choice": {"fighter": "minren", "helper": "woailuo"}}, {"choice": {"fighter": "yihu", "helper": "kon"}}],
			"stage": "现世", "rules": {"time": 90, "life": 1}, "profile": {"id": "chrome-exp-d2-p6", "inputDelay": 2, "predictionWindow": 6}, "seed": 727, "clockBaseline": 0, "setupRevision": 1}
		var hub := Hub.new(setup)
		hub.authority = host_slot
		hub.state.mode = "host-authoritative"
		hub.state.match.mode = "host-authoritative"
		var peers := []
		var rooms := []
		var coordinators := []
		for slot in 2:
			var room := Pair.FakeRoom.new()
			root.add_child(room)
			room.configure(hub, slot)
			rooms.append(room)
			var peer := Transport.new()
			root.add_child(peer)
			peer.hub = hub
			peers.append(peer)
			var coordinator := Coordinator.new()
			coordinator.cost = 100 if slot == host_slot else 200
			coordinator.scene_factory = _scene.bind(slot)
			var game: Node = _scene("probe", slot).game
			assert(coordinator.configure(game, setup, "p1" if slot == 0 else "p2", room, peer).is_empty())
			coordinators.append(coordinator)
		for slot in 2: _start.call_deferred(coordinators[slot], hub.epoch, setup.profile, slot)
		var deadline := Time.get_ticks_msec() + 15000
		while starts.size() < 2 and Time.get_ticks_msec() < deadline: await process_frame
		assert(starts.size() == 2, "startup timeout")
		assert(starts[0].is_empty() and starts[1].is_empty(), str(starts))
		assert(hub.initial_send_times.size() == 2, "Initial loss did not recover with one paced retry")
		for coordinator in coordinators: assert(coordinator.authority_slot == host_slot)
		var host: Coordinator = coordinators[host_slot]
		var guest: Coordinator = coordinators[1 - host_slot]
		for frame in range(1, 331):
			var now := Time.get_ticks_msec()
			if frame >= 30 and frame < 90: host.request_intro_skip()
			assert(guest.process_tick(now, _players(frame)[guest.local_slot]).is_empty())
			assert(host.process_tick(now, _players(frame)[host.local_slot]).is_empty())
			assert(host.game.physics_tick == frame, host.error)
			assert(guest.game.physics_tick == 0 and guest._latest_display.frame == frame)
			assert(not host.game.has_meta("rollback_checkpoint"))
			await process_frame
		hub.block_state_acks = true
		var serial_before: int = host._state_serial
		for attempt in 8: host._send_display(host._latest_display)
		assert(host._state_serial - serial_before == Authority.MAX_UNACKED_STATES, "Receiver window was not bounded")
		host._last_send_ms -= Authority.SAFETY_STALL_MS
		host._last_heartbeat_received_ms = Time.get_ticks_msec() - Authority.SAFETY_STALL_MS
		host._send_display(host._latest_display)
		assert(host._state_serial == serial_before + Authority.MAX_UNACKED_STATES, "Stalled guest received more states")
		host._last_heartbeat_received_ms = Time.get_ticks_msec()
		host._send_display(host._latest_display)
		assert(host._state_serial == serial_before + Authority.MAX_UNACKED_STATES + 1, "Lost state window could not recover")
		host._send_display(host._latest_display)
		assert(host._state_serial == serial_before + Authority.MAX_UNACKED_STATES + 1, "Recovery probe flooded")
		hub.block_state_acks = false
		guest._send_peer("authority_state_ack", {"epoch": guest.epoch, "serial": guest._received_serial})
		host._send_display(host._latest_display)
		assert(host._state_serial == serial_before + Authority.MAX_UNACKED_STATES + 2, "Guest credit did not resume fresh states")
		var frozen: int = host.game.physics_tick
		host.page_visible = false
		host.process_tick(Time.get_ticks_msec(), _players(1).p1)
		assert(host.paused and host.game.physics_tick == frozen)
		await create_timer(0.11).timeout
		host.page_visible = true
		guest.process_tick(Time.get_ticks_msec(), _players(1).p1)
		host.process_tick(Time.get_ticks_msec(), _players(1).p1)
		assert(not host.paused and not guest.paused and host.authority_slot == host_slot)
		# A late frozen snapshot may follow the reliable resume message.
		guest.paused = true
		guest.recovering = true
		host._send_display(host._latest_display)
		assert(not guest.paused and not guest.recovering)
		for attempt in 1500:
			if not host.running: break
			if not host.game.battle_intro.active and not host.game.ko_active and host.game.naruto.health > 0:
				host.game.naruto.health = 0
				host.game.naruto._check_dead(false)
			if host.intro_skippable(): host.request_intro_skip()
			guest.process_tick(Time.get_ticks_msec(), _players(1).p1)
			host.process_tick(Time.get_ticks_msec(), _players(1).p1)
			assert(host.error.is_empty() and guest.error.is_empty(), host.error + guest.error)
			await process_frame
		assert(not host.running and not guest.running and not host._terminal_result.is_empty(), "terminal receipt missing")
		var settlement_deadline := Time.get_ticks_msec() + 3000
		while not host._result_submission_complete and Time.get_ticks_msec() < settlement_deadline: await process_frame
		assert(hub.state.lastResult.reason == "host-declared/guest-received")
		assert(host._inputs.consumed_sequence > 0)
		assert(not host._rtt_samples.is_empty() and not guest._rtt_samples.is_empty())
		assert(host._projector.error.is_empty() and guest._projector.error.is_empty())
		for coordinator in coordinators: coordinator.close()
		for scene in scenes.values():
			if not scene.presentation_only: scene._goto_menu()
			scene.free()
		scenes.clear()
		for peer in peers: peer.free()
		for room in rooms: room.free()
		await process_frame
	await create_timer(0.1).timeout
	print("AUTHORITY_PAIR_OK host_slots=0,1 frames=660 guest_simulation_ticks=0")
	quit()
