extends SceneTree

const Coordinator = preload("res://online_match.gd")
const State = preload("res://simulation_state.gd")
const PairFixture = preload("res://tests/online_pair_fixture.gd")
const FakeHub = PairFixture.FakeHub
const FakeRoom = PairFixture.FakeRoom
const FakeTransport = PairFixture.FakeTransport

func _decode_graph(graph: Variant) -> Array:
	var graph_bytes: PackedByteArray = graph.hex_decode() if graph is String else graph
	return bytes_to_var(graph_bytes)


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var first_container := Node.new()
	var second_container := Node.new()
	root.add_child(first_container)
	root.add_child(second_container)
	var first := _create_game(first_container, 727)
	var second := _create_game(second_container, 727)
	first.session.codes = {"p1": 1, "p2": 2}
	first.session.ai_level = 1
	first.session.render_quality = "LOW"
	second.session.codes = {"p1": 8, "p2": 9}
	second.session.ai_level = 5
	second.session.render_quality = "HIGH"
	var setup := {
		"members": [
			{"choice": {"fighter": "minren", "helper": "woailuo"}},
			{"choice": {"fighter": "yihu", "helper": "kon"}},
		],
		"stage": "现世",
		"rules": {"time": 60, "life": 1},
		"seed": 727,
		"profile": {"id": "chrome-exp-d0-p6", "inputDelay": 0, "predictionWindow": 6},
	}
	var hub := FakeHub.new(setup)
	var first_room := FakeRoom.new()
	var first_peer := FakeTransport.new()
	var second_room := FakeRoom.new()
	var second_peer := FakeTransport.new()
	first_room.configure(hub, 0)
	first_peer.hub = hub
	second_room.configure(hub, 1)
	second_peer.hub = hub
	root.add_child(first_room)
	root.add_child(first_peer)
	root.add_child(second_room)
	root.add_child(second_peer)
	var first_match := Coordinator.new()
	var second_match := Coordinator.new()
	assert(first_match.sparse_saves and first_match.checkpoint_stride == 2)
	assert(second_match.sparse_saves and second_match.checkpoint_stride == 2)
	if OS.get_cmdline_user_args().has("--mixed-saves"):
		second_match.sparse_saves = false
		second_match.checkpoint_stride = 1
	if OS.get_cmdline_user_args().has("--full-saves"):
		first_match.sparse_saves = false
		second_match.sparse_saves = false
	if OS.get_cmdline_user_args().has("--sparse"):
		first_match.sparse_saves = true
		second_match.sparse_saves = true
		first_match.checkpoint_stride = 1
		second_match.checkpoint_stride = 1
		if OS.get_cmdline_user_args().has("--stride-two"):
			first_match.checkpoint_stride = 2
			second_match.checkpoint_stride = 2
	var first_error: String = first_match.configure(first, setup, "p1", first_room, first_peer)
	var second_error: String = second_match.configure(second, setup, "p2", second_room, second_peer)
	assert(first_error.is_empty(), "P1 configure failed: " + first_error)
	assert(second_error.is_empty(), "P2 configure failed: " + second_error)
	assert(not first.combo_hud.visible and not second.combo_hud.visible)
	assert(first.diagnostics.enabled and second.diagnostics.enabled)
	var first_state: Dictionary = first_match.save_state()
	var second_state: Dictionary = second_match.save_state()
	assert(not first_state.has("error"), str(first_state))
	assert(not second_state.has("error"), str(second_state))
	assert(first.session.codes != second.session.codes)
	assert(first.session.ai_level != second.session.ai_level)
	assert(first.session.render_quality != second.session.render_quality)
	var difference := State.first_difference(first_state, second_state)
	if not difference.is_empty():
		var left_graph: Array = _decode_graph(first_state.owners.battle.owners.battle.owners.graph)
		var right_graph: Array = _decode_graph(second_state.owners.battle.owners.battle.owners.graph)
		var graph_difference := State.first_difference(left_graph, right_graph)
		print("ONLINE_MATCH_PAIR_INITIAL_MISMATCH state=%s graph=%s" % [difference, graph_difference])
		var record_index := -1
		var match_result := RegEx.create_from_string("^\\$\\[(\\d+)\\]").search(graph_difference)
		if match_result != null:
			record_index = int(match_result.get_string(1))
		if record_index >= 0:
			print("ONLINE_MATCH_PAIR_FIRST_RECORD left=%s right=%s" % [JSON.stringify(left_graph[record_index]), JSON.stringify(right_graph[record_index])])
		quit(1)
		return
	var initial_hash: String = State.fingerprint(first_state)
	print("ONLINE_MATCH_PAIR_INITIAL_OK hash=%s local_preferences_diverge=true" % initial_hash)
	var start_results := {}
	_launch_start.call_deferred(first_match, setup.profile, start_results, "p1", hub.epoch)
	_launch_start.call_deferred(second_match, setup.profile, start_results, "p2", hub.epoch)
	for _attempt in 600:
		if start_results.get("p1_done", false) and start_results.get("p2_done", false):
			break
		await process_frame
	assert(start_results.get("p1_done", false), "P1 did not complete the start barrier")
	assert(start_results.get("p2_done", false), "P2 did not complete the start barrier")
	assert(str(start_results.p1).is_empty(), "P1 start failed: " + str(start_results.p1))
	assert(str(start_results.p2).is_empty(), "P2 start failed: " + str(start_results.p2))
	assert(first_match.running and second_match.running, "Both coordinators must pass match_ready")
	print("ONLINE_MATCH_PAIR_STARTED_OK")
	var neutral := _held_input(false)
	var time_origin := Time.get_ticks_msec()
	for tick in range(1, 4):
		var tick_error := _step_pair(first_match, second_match, time_origin + tick * 33, neutral, neutral)
		assert(tick_error.is_empty(), tick_error)
		await process_frame
	assert(first_match.rollback.frontier == 3 and second_match.rollback.frontier == 3)
	_align_pair(first_match, second_match, neutral)
	difference = State.first_difference(first_match.save_state(), second_match.save_state())
	assert(difference.is_empty(), "Same input/clock state differs at frame 3: " + difference)
	hub.hold_p2_to_p1 = true
	for tick in range(4, 13):
		var remote_held := _held_input(tick == 5)
		var tick_error := _step_pair(first_match, second_match, time_origin + tick * 33, neutral, remote_held)
		assert(tick_error.is_empty(), tick_error)
		await process_frame
	assert(not hub.held_from_p2.is_empty(), "Fake network did not hold P2 messages")
	hub.release_p2_messages()
	assert(first_match.rollback.rollback_count > 0, "Late P2 input did not trigger rollback correction")
	var bootstrap_corrections: int = first_match.rollback.rollback_count
	assert(bootstrap_corrections == 1, "One input drain must correct once")
	for tick in range(13, 19):
		var tick_error := _step_pair(first_match, second_match, time_origin + tick * 33, neutral, neutral)
		assert(tick_error.is_empty(), tick_error)
		await process_frame
	_align_pair(first_match, second_match, neutral)
	assert(first_match.rollback.frontier == second_match.rollback.frontier,
		"Peers did not return to the same simulation frontier: %d vs %d" % [first_match.rollback.frontier, second_match.rollback.frontier])
	_align_pair(first_match, second_match, neutral)
	difference = State.first_difference(first_match.save_state(), second_match.save_state())
	assert(difference.is_empty(), "Late JSON-roundtripped input did not converge: " + difference)
	print("ONLINE_MATCH_PAIR_BOOTSTRAP_CORRECTION_OK frame=%d p1_rollback_count=%d json_roundtrip=true" % [
		first_match.rollback.frontier, first_match.rollback.rollback_count,
	])
	assert(second_match.request_intro_skip().is_empty(), "P2 could not request an intro skip")
	assert(first_match._intro_skip_frames == second_match._intro_skip_frames and not first_match._intro_skip_frames.is_empty(),
		"Host intro-skip commit was not delivered in order to both peers")
	for target in first_match._intro_skip_frames:
		assert(int(target) > first_match.rollback.frontier, "Intro-skip target was not scheduled in the future")
	print("ONLINE_MATCH_PAIR_INTRO_SKIP_ORDERED_OK target=%d" % int(first_match._intro_skip_frames.keys()[0]))
	var intro_was_completed := false
	var combat_start_tick := -1
	var p1_start_x: float = first.naruto.position.x
	var p2_start_x: float = first.ichigo.position.x
	var p1_health_before_fight: float = first.naruto.health
	var p2_health_before_fight: float = first.ichigo.health
	var saw_helper_activation := false
	var late_combat_input_released := false
	for tick in range(19, 601):
		var p1_buttons: Array[String] = []
		var p2_buttons: Array[String] = []
		if not first.battle_intro.active and combat_start_tick < 0:
			combat_start_tick = tick
		if combat_start_tick >= 0:
			var combat_frame: int = tick - combat_start_tick
			if combat_frame >= 1 and combat_frame <= 24:
				p1_buttons.append("right")
				p2_buttons.append("left")
			if combat_frame >= 26 and combat_frame <= 55:
				p1_buttons.append("attack")
				p2_buttons.append("attack")
			if combat_frame == 70:
				p1_buttons.append("summon")
			if combat_frame == 75:
				p2_buttons.append("summon")
			if combat_frame == 25:
				hub.hold_p2_to_p1 = true
			if combat_frame == 30:
				hub.release_p2_messages()
				late_combat_input_released = true
		var p1_held := _held_buttons(p1_buttons)
		var p2_held := _held_buttons(p2_buttons)
		var tick_error := _step_pair(first_match, second_match, time_origin + tick * 33, p1_held, p2_held)
		assert(tick_error.is_empty(), "frame %d %s" % [tick, tick_error])
		if not first.battle_intro.active:
			intro_was_completed = true
			if first.naruto_helper.attacking or first.ichigo_helper.attacking:
				saw_helper_activation = true
		await process_frame
	assert(intro_was_completed and combat_start_tick >= 0 and not second.battle_intro.active,
		"Ordered intro skip did not finish the intro on both peers")
	assert(first_match.rollback.rollback_count > bootstrap_corrections, "Delayed combat input did not cause an additional rollback")
	assert(late_combat_input_released, "Delayed combat input was not released")
	assert(first.naruto.health < p1_health_before_fight or first.ichigo.health < p2_health_before_fight,
		"Combat inputs did not produce a real hit or health change")
	assert(first.naruto.position.x > p1_start_x and first.ichigo.position.x < p2_start_x,
		"Players did not move toward each other in the post-intro input sequence")
	for slot in [0, 1]:
		for expected_frame in [30, 60, 90]:
			assert(hub.state_hash_frames[slot].has(expected_frame), "Slot %d never sent confirmed frame hash %d" % [slot, expected_frame])
	assert(first_match._local_hashes.is_empty() and first_match._remote_hashes.is_empty(), "Periodic confirmed hashes remain unmatched")
	assert(second_match._local_hashes.is_empty() and second_match._remote_hashes.is_empty(), "Peer periodic confirmed hashes remain unmatched")
	_align_pair(first_match, second_match, neutral)
	difference = State.first_difference(first_match.save_state(), second_match.save_state())
	assert(difference.is_empty(), "Fight states differ after live attack/movement/helper inputs: " + difference)
	print("ONLINE_MATCH_PAIR_FIGHT_HASH_OK frame=%d hashes=30,60,90 real_hit=true helper_activity=%s" % [
		first_match.rollback.frontier, str(saw_helper_activation),
	])
	var control_errors: Array[String] = []
	var on_pause := func(request: Dictionary) -> void:
		var response: String = second_match.respond_pause(str(request.get("id", "")), true)
		if not response.is_empty():
			control_errors.append(response)
	second_match.pause_requested.connect(on_pause)
	var on_resume := func(request: Dictionary) -> void:
		var response: String = second_match.respond_resume(str(request.get("id", "")), true)
		if not response.is_empty():
			control_errors.append(response)
	second_match.resume_requested.connect(on_resume)
	assert(first_match.request_pause().is_empty(), "P1 pause request failed")
	var control_now := time_origin + 600 * 33
	for _attempt in 30:
		control_now += 33
		var tick_error := _step_pair(first_match, second_match, control_now, neutral, neutral)
		assert(tick_error.is_empty(), "pause barrier tick failed: " + tick_error)
		await process_frame
		if first_match.paused and second_match.paused:
			break
	assert(control_errors.is_empty(), "Pause response failed: " + "; ".join(control_errors))
	assert(first_match.paused and second_match.paused, "Both peers did not commit the pause barrier")
	assert(first_match.rollback.frontier == second_match.rollback.frontier, "Pause did not stop both peers at the same frame")
	_align_pair(first_match, second_match, neutral)
	difference = State.first_difference(first_match.save_state(), second_match.save_state())
	assert(difference.is_empty(), "Peers disagreed on the confirmed pause state: " + difference)
	var pause_frame: int = first_match.rollback.frontier
	print("ONLINE_MATCH_PAIR_PAUSE_BARRIER_OK frame=%d equal_hash=true" % pause_frame)
	assert(first_match.request_resume().is_empty(), "P1 resume request failed")
	for _attempt in 10:
		control_now += 33
		var tick_error := _step_pair(first_match, second_match, control_now, neutral, neutral)
		assert(tick_error.is_empty(), "resume barrier tick failed: " + tick_error)
		await process_frame
		if not first_match.paused and not second_match.paused:
			break
	assert(control_errors.is_empty(), "Resume response failed: " + "; ".join(control_errors))
	assert(not first_match.paused and not second_match.paused, "Both peers did not commit the resume barrier")
	_align_pair(first_match, second_match, neutral)
	difference = State.first_difference(first_match.save_state(), second_match.save_state())
	assert(difference.is_empty(), "Peers diverged while resuming: " + difference)
	print("ONLINE_MATCH_PAIR_RESUME_BARRIER_OK frame=%d equal_hash=true" % first_match.rollback.frontier)
	var recovery_events: Array[String] = []
	first_match.recovery_changed.connect(func(state: String) -> void: recovery_events.append("p1:" + state))
	second_match.recovery_changed.connect(func(state: String) -> void: recovery_events.append("p2:" + state))
	first_peer.set_link_connected(false)
	second_peer.set_link_connected(false)
	assert(first_match.recovering and second_match.recovering, "Both peers did not enter recovery after transport loss")
	first_peer.set_link_connected(true)
	second_peer.set_link_connected(true)
	var recovery_previous_ms := maxi(first_match._process_now_ms, second_match._process_now_ms)
	var recovery_wall_ms := Time.get_ticks_msec()
	var recovery_now := maxi(control_now, recovery_wall_ms)
	print("ONLINE_MATCH_PAIR_RECOVERY_CLOCK previous_ms=%d wall_now_ms=%d supplied_now_ms=%d raw_delta_ms=%d" % [
		recovery_previous_ms, recovery_wall_ms, recovery_now, recovery_wall_ms - recovery_previous_ms,
	])
	assert(recovery_now >= recovery_previous_ms, "Recovery clock moved backward: previous=%d now=%d" % [recovery_previous_ms, recovery_now])
	assert(recovery_now >= first_match._disconnect_started_ms and recovery_now >= second_match._disconnect_started_ms,
		"Recovery tick preceded disconnect start: now=%d p1=%d p2=%d" % [
			recovery_now, first_match._disconnect_started_ms, second_match._disconnect_started_ms,
		])
	for _attempt in 40:
		recovery_now += 50
		var tick_error := _step_pair(first_match, second_match, recovery_now, neutral, neutral)
		assert(tick_error.is_empty(), "recovery tick failed: " + tick_error)
		await process_frame
		if not first_match.recovering and not second_match.recovering:
			break
	assert(not first_match.recovering and not second_match.recovering, "Recovered channels did not reconcile")
	assert(recovery_events.has("p1:reconciled") and recovery_events.has("p2:reconciled"),
		"Both peers did not complete the recovery comparison/commit protocol: " + str(recovery_events))
	_align_pair(first_match, second_match, neutral)
	difference = State.first_difference(first_match.save_state(), second_match.save_state())
	assert(difference.is_empty(), "Peers diverged after short recovery: " + difference)
	print("ONLINE_MATCH_PAIR_SHORT_RECOVERY_OK both_reconciled=true equal_hash=true")
	var abort_reports: Array[Dictionary] = []
	first_match.diagnostic_abort.connect(func(report: Dictionary) -> void: abort_reports.append(report))
	first_peer.set_link_connected(false)
	second_peer.set_link_connected(false)
	assert(first_match.recovering and second_match.recovering, "Peers did not begin the timeout recovery window")
	var timeout_origin: int = first_match._disconnect_started_ms
	var before_deadline_error := first_match.process_tick(timeout_origin + Coordinator.RECOVERY_MS - 1, neutral)
	assert(before_deadline_error.is_empty(), "Recovery aborted before its 30-second deadline: %s (origin=%d current=%d recovery_start=%d)" % [
		before_deadline_error, timeout_origin, first_match._process_now_ms, first_match._recovery_started_ms,
	])
	assert(first_match.running and first_match.recovering, "Peer stopped before the 30-second deadline")
	first_match.process_tick(timeout_origin + Coordinator.RECOVERY_MS, neutral)
	assert(first_match.error == "peer_disconnect_timeout" and not first_match.running,
		"Peer disconnect did not abort without a winner at 30 seconds")
	assert(not abort_reports.is_empty() and abort_reports.back().get("details", {}).get("winner", "missing") == null,
		"Disconnect timeout diagnostics did not record a null winner")
	print("ONLINE_MATCH_PAIR_TIMEOUT_ABORT_OK fake_elapsed_ms=30000 winner=null")
	print("ONLINE_MATCH_PAIR_SMOKE_OK initial_hash=%s frame=%d p1_rollback_count=%d json_roundtrip=true" % [
		initial_hash, first_match.rollback.frontier, first_match.rollback.rollback_count,
	])
	second_match.pause_requested.disconnect(on_pause)
	second_match.resume_requested.disconnect(on_resume)
	on_pause = Callable()
	on_resume = Callable()
	first_match.close()
	second_match.close()
	assert(hub.peers.is_empty(), "Closing both transports must release hub registrations")
	var second_match_ref: WeakRef = weakref(second_match)
	second_match = null
	assert(second_match_ref.get_ref() == null, "Pause/resume callbacks retained the closed coordinator")
	assert(not first.combo_hud.has_meta("suppress_display"))
	assert(not second.combo_hud.has_meta("suppress_display"))
	first_room.free()
	first_peer.free()
	second_room.free()
	second_peer.free()
	first._goto_menu()
	second._goto_menu()
	first.free()
	second.free()
	first_container.free()
	second_container.free()
	await process_frame
	var result_setup: Dictionary = setup.duplicate(true)
	result_setup.seed = 891
	hub.prepare_next_epoch(result_setup, "6ba7b811-9dad-41d1-80b4-00c04fd430c8", result_setup.seed)
	var result_first_container := Node.new()
	var result_second_container := Node.new()
	root.add_child(result_first_container)
	root.add_child(result_second_container)
	var result_first_game := _create_game(result_first_container, result_setup.seed)
	var result_second_game := _create_game(result_second_container, result_setup.seed)
	for result_game in [result_first_game, result_second_game]:
		result_game.ko_state["_root.p2ws"] = 2
		result_game.naruto.health = 0.0
		assert(result_game.naruto._check_dead(false), "Test fixture did not enter the source fighter KO path")
	var result_first_room := FakeRoom.new()
	var result_second_room := FakeRoom.new()
	var result_first_peer := FakeTransport.new()
	var result_second_peer := FakeTransport.new()
	result_first_room.configure(hub, 0)
	result_first_peer.hub = hub
	result_first_peer.game = result_first_game
	result_second_room.configure(hub, 1)
	result_second_peer.hub = hub
	result_second_peer.game = result_second_game
	root.add_child(result_first_room)
	root.add_child(result_first_peer)
	root.add_child(result_second_room)
	root.add_child(result_second_peer)
	var result_first_match := Coordinator.new()
	var result_second_match := Coordinator.new()
	assert(result_first_match.configure(result_first_game, result_setup, "p1", result_first_room, result_first_peer).is_empty())
	assert(result_second_match.configure(result_second_game, result_setup, "p2", result_second_room, result_second_peer).is_empty())
	var result_start_results := {}
	_launch_start.call_deferred(result_first_match, result_setup.profile, result_start_results, "p1", hub.epoch)
	_launch_start.call_deferred(result_second_match, result_setup.profile, result_start_results, "p2", hub.epoch)
	for _attempt in 600:
		if result_start_results.get("p1_done", false) and result_start_results.get("p2_done", false):
			break
		await process_frame
	assert(result_start_results.get("p1_done", false) and result_start_results.get("p2_done", false),
		"Result round start barrier did not complete")
	assert(str(result_start_results.p1).is_empty() and str(result_start_results.p2).is_empty(),
		"Result round start failed: %s / %s" % [str(result_start_results.p1), str(result_start_results.p2)])
	assert(result_second_match.request_intro_skip().is_empty(), "Result round intro skip request failed")
	print("ONLINE_MATCH_PAIR_SOURCE_KO_FIXTURE_OK fighter_check_dead=true")
	var results_confirmed: Dictionary = {"p1": [], "p2": []}
	var room_results_committed: Dictionary = {"p1": [], "p2": []}
	result_first_match.result_confirmed.connect(func(value: Dictionary) -> void: results_confirmed.p1.append(value))
	result_second_match.result_confirmed.connect(func(value: Dictionary) -> void: results_confirmed.p2.append(value))
	result_first_match.room_result_committed.connect(func(value: Dictionary) -> void: room_results_committed.p1.append(value))
	result_second_match.room_result_committed.connect(func(value: Dictionary) -> void: room_results_committed.p2.append(value))
	hub.hold_p2_result_to_p1 = true
	var result_neutral := _held_input(false)
	var result_now := Time.get_ticks_msec()
	var p2_result_submitted := false
	for result_frame in range(1, 601):
		result_now += 33
		var tick_error := _step_pair(result_first_match, result_second_match, result_now,
			result_neutral, result_neutral)
		assert(tick_error.is_empty(), "Result round frame %d failed: %s" % [result_frame, tick_error])
		if result_frame % 10 == 0:
			await process_frame
			var current_match: Variant = hub.state.get("match")
			if current_match is Dictionary and current_match.results[1] is Dictionary \
				and not hub.held_results_from_p2.is_empty():
				p2_result_submitted = true
				break
			if not result_first_match.error.is_empty() or not result_second_match.error.is_empty():
				break
	if not p2_result_submitted:
		var debug_match: Variant = hub.state.get("match")
		print("ONLINE_MATCH_PAIR_RESULT_DEBUG confirmed=%s room_committed=%s p1={error:%s,running:%s,local:%s,remote:%s,submitting:%s} p2={error:%s,running:%s,local:%s,remote:%s,submitting:%s}" % [
			str(results_confirmed), str(room_results_committed), str(result_first_match.error),
			str(result_first_match.running), str(result_first_match._local_results), str(result_first_match._remote_result),
			str(result_first_match._result_submission_started), str(result_second_match.error),
			str(result_second_match.running), str(result_second_match._local_results), str(result_second_match._remote_result),
			str(result_second_match._result_submission_started),
		])
		push_error("Result smoke timeout frame=%d p1_terminal=%s p2_terminal=%s p1_ko_active=%s p2_ko_active=%s match_results=%s held_peer_results=%d" % [
			result_first_match.rollback.frontier, str(result_first_game.ko_terminal_pending),
			str(result_second_game.ko_terminal_pending), str(result_first_game.ko_active),
			str(result_second_game.ko_active), str(debug_match.get("results", [])) if debug_match is Dictionary else "missing",
			hub.held_results_from_p2.size(),
		])
		quit(1)
		return
	assert(result_first_peer.result_sent_from_source_terminal and result_second_peer.result_sent_from_source_terminal,
		"Both result messages must originate while each battle is at its source KO terminal state")
	assert(results_confirmed.p1.is_empty() and results_confirmed.p2.size() == 1,
		"One peer confirmation should wait while P2's result packet is held: %s" % str(results_confirmed))
	assert(hub.state.phase == "active" and hub.state.lastResult == null and hub.state.match.results[0] == null,
		"Room committed before both result submissions arrived")
	assert(room_results_committed.p1.is_empty() and room_results_committed.p2.is_empty(),
		"A peer reported room result commitment before service agreement")
	var agreed_result: Dictionary = results_confirmed.p2[0].duplicate(true)
	assert(agreed_result.epoch == hub.epoch and agreed_result.winner == 1,
		"Source KO result had an unexpected epoch or winner: " + str(agreed_result))
	hub.release_p2_result()
	for _attempt in 90:
		if room_results_committed.p1.size() == 1 and room_results_committed.p2.size() == 1:
			break
		await process_frame
	assert(results_confirmed.p1.size() == 1 and results_confirmed.p2.size() == 1,
		"Both peers did not confirm the same source result")
	assert(room_results_committed.p1.size() == 1 and room_results_committed.p2.size() == 1,
		"Room result was not observed by both clients after service confirmation")
	assert(hub.state.phase == "lobby" and hub.state.match == null
		and hub.state.lastResult.epoch == agreed_result.epoch
		and hub.state.lastResult.reason == "agreed" and hub.state.lastResult.winner == agreed_result.winner,
		"Fake service did not mirror the real agreed-result room transition")
	print("ONLINE_MATCH_PAIR_RESULT_COMMIT_OK source_ko=true p1_waited_for_peer=true room_waited_for_both=true winner=1")
	result_first_match.close()
	result_second_match.close()
	result_first_room.free()
	result_first_peer.free()
	result_second_room.free()
	result_second_peer.free()
	result_first_game._goto_menu()
	result_second_game._goto_menu()
	result_first_game.free()
	result_second_game.free()
	result_first_container.free()
	result_second_container.free()
	await process_frame
	var previous_epoch := hub.epoch
	var next_setup: Dictionary = setup.duplicate(true)
	next_setup.seed = 992
	var next_epoch := "6ba7b812-9dad-41d1-80b4-00c04fd430c8"
	hub.prepare_next_epoch(next_setup, next_epoch, next_setup.seed)
	var next_first_container := Node.new()
	var next_second_container := Node.new()
	root.add_child(next_first_container)
	root.add_child(next_second_container)
	var next_first_game := _create_game(next_first_container, next_setup.seed)
	var next_second_game := _create_game(next_second_container, next_setup.seed)
	var next_first_room := FakeRoom.new()
	var next_second_room := FakeRoom.new()
	var next_first_peer := FakeTransport.new()
	var next_second_peer := FakeTransport.new()
	next_first_room.configure(hub, 0)
	next_first_peer.hub = hub
	next_second_room.configure(hub, 1)
	next_second_peer.hub = hub
	root.add_child(next_first_room)
	root.add_child(next_first_peer)
	root.add_child(next_second_room)
	root.add_child(next_second_peer)
	var next_first_match := Coordinator.new()
	var next_second_match := Coordinator.new()
	assert(next_first_match.configure(next_first_game, next_setup, "p1", next_first_room, next_first_peer).is_empty())
	assert(next_second_match.configure(next_second_game, next_setup, "p2", next_second_room, next_second_peer).is_empty())
	var next_start_results := {}
	_launch_start.call_deferred(next_first_match, next_setup.profile, next_start_results, "p1", next_epoch)
	_launch_start.call_deferred(next_second_match, next_setup.profile, next_start_results, "p2", next_epoch)
	for _attempt in 600:
		if next_start_results.get("p1_done", false) and next_start_results.get("p2_done", false):
			break
		await process_frame
	assert(next_start_results.get("p1_done", false) and next_start_results.get("p2_done", false)
		and str(next_start_results.p1).is_empty() and str(next_start_results.p2).is_empty(),
		"New epoch start failed after an agreed match result")
	assert(previous_epoch != next_first_match.epoch and next_first_match.running and next_second_match.running,
		"Rematch did not start under a fresh epoch")
	next_first_match.receive_peer_message("reliable", "result", agreed_result, hub.next_peer_sequence[1] + 1)
	assert(next_first_match.error.is_empty() and next_first_match.running,
		"A result from the previous epoch poisoned the rematch")
	print("ONLINE_MATCH_PAIR_NEW_EPOCH_OK previous_result_rejected=true epoch_changed=true")
	next_first_match.close()
	next_second_match.close()
	next_first_room.free()
	next_first_peer.free()
	next_second_room.free()
	next_second_peer.free()
	next_first_game._goto_menu()
	next_second_game._goto_menu()
	next_first_game.free()
	next_second_game.free()
	next_first_container.free()
	next_second_container.free()
	await process_frame
	quit()


func _launch_start(coordinator: Object, profile: Dictionary, results: Dictionary, slot: String, match_epoch: String) -> void:
	var start_error: String = await coordinator.start(match_epoch, profile, "p1")
	results[slot] = start_error
	results[slot + "_done"] = true


func _step_pair(first_match: Object, second_match: Object, now_ms: int, first_input: Dictionary, second_input: Dictionary) -> String:
	var first_error: String = first_match.process_tick(now_ms, first_input)
	var second_error: String = second_match.process_tick(now_ms, second_input)
	if not first_error.is_empty():
		return "P1 tick failed: " + first_error
	if not second_error.is_empty():
		return "P2 tick failed: " + second_error
	return ""


func _held_input(attack: bool) -> Dictionary:
	var buttons: Array[String] = []
	if attack:
		buttons.append("attack")
	return _held_buttons(buttons)


func _held_buttons(buttons: Array[String]) -> Dictionary:
	var held := {}
	for button in preload("res://keyboard_input_source.gd").BUTTONS:
		held[button] = false
	for button in buttons:
		held[button] = true
	return held


func _create_game(parent: Node, seed: int) -> Node:
	var game: Node = load("res://main.tscn").instantiate()
	parent.add_child(game)
	game.set_physics_process(false)
	game.set_process(false)
	game.ko_recorded_timers = true
	game.recorded_training_timers = true
	game.source_random.use_seed(seed)
	game.source_clock.use_explicit_time(0)
	var roster_error: String = game.configure_diagnostic_roster({
		"p1": {"resourcePath": "res://generated/fighters/minren", "helper": {"resourcePath": "res://generated/helpers/woailuo"}},
		"p2": {"resourcePath": "res://generated/fighters/yihu", "helper": {"resourcePath": "res://generated/helpers/kon"}},
	})
	assert(roster_error.is_empty(), roster_error)
	game._load_selected_stage("现世")
	game._enter_current_fight(3)
	game.battle_intro.recorded_polling = true
	for timer in game.title_menu.find_children("*", "Timer", true, false):
		timer.stop()
	return game


func _align_pair(first: Object, second: Object, held: Dictionary) -> void:
	# Independent clocks permit temporary frontier differences. Compare complete
	# checkpoints only after delivering both peers to the same simulation frame.
	for attempt in 32:
		if first.rollback.frontier == second.rollback.frontier: return
		var behind: Object = first if first.rollback.frontier < second.rollback.frontier else second
		assert(behind.process_tick(behind._process_now_ms, held).is_empty())
	assert(false, "Peers could not reach a common frame")
