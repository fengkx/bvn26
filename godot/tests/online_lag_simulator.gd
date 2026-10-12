extends SceneTree

const Coordinator = preload("res://online_match.gd")
const State = preload("res://simulation_state.gd")
const PairFixture = preload("res://tests/online_pair_fixture.gd")
const BUTTONS = preload("res://keyboard_input_source.gd").BUTTONS
const FRAME_INTERVAL_MS := 1000.0 / 30.0
const MIN_COMMON_HASHES := 3
const DEFAULT_DURATION_MS := 10_000
const DEFAULT_PROFILE := {"id": "chrome-exp-d2-p6", "inputDelay": 2, "predictionWindow": 6}
const FIELD_LOGS := {
	"p1": {
		"path": "evidence/online/network-lag/p1-net-2026-09-29.json",
		"sha256": "bf45ff68ca8c3555111461c8be600fd4cca97b370af7ad82c6cf91e35498d18d",
	},
	"p2": {
		"path": "evidence/online/network-lag/p2-net-2026-09-29.json",
		"sha256": "4417e022c24926d80ab163e90539b6f03551fca5c80080bcffd6daebfa091ade",
	},
}
const TAPE_PATH := "res://tests/rollback_performance_user_log_r01.json"
const SCENARIO_DEFINITIONS := {
	"lan": {"latency_ms": 2.0, "jitter_ms": 0.0, "loss_rate": 0.0, "cost_mode": "fast", "seed": 40401},
	"turn40": {"latency_ms": 20.0, "jitter_ms": 5.0, "loss_rate": 0.0, "cost_mode": "fast", "seed": 40402},
	"turn40-slowhost": {"latency_ms": 20.0, "jitter_ms": 5.0, "loss_rate": 0.0, "cost_mode": "slow_host", "seed": 40403},
	"turn40-fixedskip": {"latency_ms": 20.0, "jitter_ms": 5.0, "loss_rate": 0.0, "cost_mode": "fast", "seed": 40404, "fixed_skip": true},
	"turn100": {"latency_ms": 50.0, "jitter_ms": 15.0, "loss_rate": 0.0, "cost_mode": "slow_host", "seed": 40405},
	"lossy": {"latency_ms": 20.0, "jitter_ms": 5.0, "loss_rate": 0.03, "cost_mode": "slow_host", "seed": 40406},
}


class PacketRecorder extends RefCounted:
	var delivered: Array[Dictionary] = []

	func deliver_peer_message(message: Dictionary) -> void:
		delivered.append(message)


class VirtualNetwork extends RefCounted:
	var hub: Object
	var scenario: Dictionary
	var now_ms := 0.0
	var pending: Array[Dictionary] = []
	var peer_hashes := [{}, {}]
	var _rngs: Array[Dictionary] = [{}, {}]
	var _last_reliable_arrival_ms := [0.0, 0.0]
	var _last_reliable_sequence := [{}, {}]
	var _last_unordered_sequence := [{}, {}]
	var _stats := {
		"sent": 0,
		"sentByChannel": {"reliable": 0, "input": 0},
		"delivered": 0,
		"deliveredByChannel": {"reliable": 0, "input": 0},
		"lost": 0,
		"lostByChannel": {"reliable": 0, "input": 0},
		"reorderedUnordered": 0,
		"reliableOrderViolations": 0,
		"peakQueued": 0,
		"byDirection": [
			{"sent": 0, "delivered": 0, "lost": 0},
			{"sent": 0, "delivered": 0, "lost": 0},
		],
	}

	func _init(fake_hub: Object, configuration: Dictionary) -> void:
		hub = fake_hub
		scenario = configuration.duplicate(true)

	func send_from_peer(sender_slot: int, message: Dictionary) -> void:
		var channel := str(message.get("channel", "reliable"))
		if channel not in ["reliable", "input"]:
			return
		var direction := _direction_config(sender_slot)
		var direction_stats: Dictionary = _stats.byDirection[sender_slot]
		_stats.sent = int(_stats.sent) + 1
		_stats.sentByChannel[channel] = int(_stats.sentByChannel[channel]) + 1
		direction_stats.sent = int(direction_stats.sent) + 1
		var envelope: Dictionary = message.get("envelope", {})
		var sequence := int(message.get("channel_sequence", envelope.get("seq", 0)))
		var kind := str(envelope.get("type", ""))
		if kind == "state_hash":
			var payload: Dictionary = envelope.get("payload", {})
			peer_hashes[sender_slot][int(payload.get("frame", -1))] = str(payload.get("hash", ""))

		if channel == "input" and _stream_rng(sender_slot, "loss").randf() < float(scenario.get("loss_rate", 0.0)):
			_stats.lost = int(_stats.lost) + 1
			_stats.lostByChannel.input = int(_stats.lostByChannel.input) + 1
			direction_stats.lost = int(direction_stats.lost) + 1
			return

		var latency_ms := float(direction.get("latency_ms", scenario.get("latency_ms", 0.0)))
		var jitter_ms := float(direction.get("jitter_ms", scenario.get("jitter_ms", 0.0)))
		var jitter := _stream_rng(sender_slot, "delay").randf_range(-jitter_ms, jitter_ms) if jitter_ms > 0.0 else 0.0
		var sampled_arrival_ms := now_ms + maxf(0.0, latency_ms + jitter)
		var arrival_ms := sampled_arrival_ms
		if channel == "reliable":
			arrival_ms = maxf(arrival_ms, float(_last_reliable_arrival_ms[sender_slot]))
			_last_reliable_arrival_ms[sender_slot] = arrival_ms
		pending.append({
			"sender": sender_slot,
			"receiver": 1 - sender_slot,
			"channel": channel,
			"sequence": sequence,
			"sampled_arrival_ms": sampled_arrival_ms,
			"arrival_ms": arrival_ms,
			"message": message,
		})
		_stats.peakQueued = maxi(int(_stats.peakQueued), pending.size())

	func drain_for_peer(receiver_slot: int, at_ms: float) -> int:
		var ready: Array[Dictionary] = []
		var remaining: Array[Dictionary] = []
		for packet in pending:
			if int(packet.receiver) == receiver_slot and float(packet.arrival_ms) <= at_ms + 0.0001:
				ready.append(packet)
			else:
				remaining.append(packet)
		pending = remaining
		ready.sort_custom(Callable(self, "_packet_before"))
		var delivered_count := 0
		for packet in ready:
			var sender := int(packet.sender)
			var channel := str(packet.channel)
			var sequence := int(packet.sequence)
			if channel == "input":
				var previous := int(_last_unordered_sequence[receiver_slot].get(sender, 0))
				if previous > 0 and sequence < previous:
					_stats.reorderedUnordered = int(_stats.reorderedUnordered) + 1
				_last_unordered_sequence[receiver_slot][sender] = maxi(previous, sequence)
			else:
				var previous := int(_last_reliable_sequence[receiver_slot].get(sender, 0))
				if previous > 0 and sequence != previous + 1:
					_stats.reliableOrderViolations = int(_stats.reliableOrderViolations) + 1
				_last_reliable_sequence[receiver_slot][sender] = sequence
			hub.deliver_peer_message(packet.message)
			_stats.delivered = int(_stats.delivered) + 1
			_stats.deliveredByChannel[channel] = int(_stats.deliveredByChannel[channel]) + 1
			delivered_count += 1
			var direction_stats: Dictionary = _stats.byDirection[sender]
			direction_stats.delivered = int(direction_stats.delivered) + 1
		return delivered_count

	func summary() -> Dictionary:
		var result: Dictionary = _stats.duplicate(true)
		result["stillQueued"] = pending.size()
		var queued_by_channel := {"reliable": 0, "input": 0}
		for packet in pending:
			var channel := str(packet.channel)
			queued_by_channel[channel] = int(queued_by_channel[channel]) + 1
		result["queuedByChannel"] = queued_by_channel
		var reliable_accounted := int(_stats.deliveredByChannel.reliable) + int(queued_by_channel.reliable)
		result["reliableConservation"] = int(_stats.sentByChannel.reliable) == reliable_accounted
		result["reliableOrderVerified"] = int(_stats.reliableOrderViolations) == 0
		result["lossPolicy"] = {
			"configuredInputLossRate": float(scenario.get("loss_rate", 0.0)),
			"affectedChannel": "input",
			"observedInputLoss": int(_stats.lostByChannel.input),
		}
		return result

	func _packet_before(left: Dictionary, right: Dictionary) -> bool:
		var left_channel := str(left.channel)
		var right_channel := str(right.channel)
		var left_rank := 0 if left_channel == "reliable" else 1
		var right_rank := 0 if right_channel == "reliable" else 1
		if left_rank != right_rank:
			return left_rank < right_rank
		if left_channel == "reliable":
			return int(left.sequence) < int(right.sequence)
		if float(left.arrival_ms) != float(right.arrival_ms):
			return float(left.arrival_ms) < float(right.arrival_ms)
		return int(left.sequence) < int(right.sequence)

	func _direction_config(sender_slot: int) -> Dictionary:
		var directions: Variant = scenario.get("directions", [])
		if directions is Array and directions.size() > sender_slot and directions[sender_slot] is Dictionary:
			return directions[sender_slot]
		return {}

	func _stream_rng(sender_slot: int, stream: String) -> RandomNumberGenerator:
		if not _rngs[sender_slot].has(stream):
			var rng := RandomNumberGenerator.new()
			var stream_id := 1 if stream == "loss" else 0
			rng.seed = int(scenario.get("seed", 1)) + sender_slot * 1009 + stream_id * 104729
			_rngs[sender_slot][stream] = rng
		return _rngs[sender_slot][stream]


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var options := _parse_args()
	if bool(options.self_test):
		var self_test := _network_semantics_smoke()
		var record_test := _record_write_smoke()
		self_test["recordWrite"] = record_test
		self_test["ok"] = bool(self_test.get("ok", false)) and bool(record_test.get("ok", false))
		print(JSON.stringify(self_test))
		quit(0 if bool(self_test.get("ok", false)) else 1)
		return
	var record_path := ""
	if not str(options.get("record", "")).is_empty():
		var prepared_record := _prepare_record_path(str(options.record))
		if not str(prepared_record.get("error", "")).is_empty():
			push_error("Simulator record path is not writable: " + str(prepared_record.error))
			quit(2)
			return
		record_path = str(prepared_record.path)
	var scenario_names: Array[String] = []
	if bool(options.all):
		for name in SCENARIO_DEFINITIONS.keys():
			scenario_names.append(str(name))
		scenario_names.sort()
	else:
		var chosen := str(options.get("scenario", "lan"))
		if not SCENARIO_DEFINITIONS.has(chosen):
			push_error("Unknown lag scenario: " + chosen)
			quit(2)
			return
		scenario_names.append(chosen)
	var requested_duration_ms := int(options.get("duration_ms", -1))
	var duration_ms := requested_duration_ms if requested_duration_ms > 0 else DEFAULT_DURATION_MS
	var outputs: Array[Dictionary] = []
	var exit_code := 0
	for scenario_name in scenario_names:
		var scenario := _materialize_scenario(scenario_name, options, duration_ms)
		var result: Dictionary = await _run_scenario(scenario)
		outputs.append(result)
		print(JSON.stringify(result))
		if not bool(result.get("ok", false)):
			exit_code = 1
	if not record_path.is_empty():
		var record_file := FileAccess.open(record_path, FileAccess.WRITE)
		if record_file == null:
			push_error("Could not write simulator output: " + record_path)
			exit_code = 1
		else:
			for result in outputs:
				record_file.store_line(JSON.stringify(result))
			record_file.close()
	quit(exit_code)


func _parse_args() -> Dictionary:
	var result := {"scenario": "lan", "all": false, "self_test": false, "duration_ms": -1, "seed": -1, "record": ""}
	for argument in OS.get_cmdline_user_args():
		if argument in ["--sparse", "--pacing", "--stride-two"]: continue
		if argument == "--all":
			result.all = true
		elif argument == "--self-test":
			result.self_test = true
		elif argument.begins_with("--scenario="):
			result.scenario = argument.trim_prefix("--scenario=")
		elif argument.begins_with("--duration-ms="):
			result.duration_ms = int(argument.trim_prefix("--duration-ms="))
		elif argument.begins_with("--seed="):
			result.seed = int(argument.trim_prefix("--seed="))
		elif argument.begins_with("--record="):
			result.record = argument.trim_prefix("--record=")
	return result


func _record_write_smoke() -> Dictionary:
	var requested_path := "/private/tmp/lag04-record-smoke-%d.jsonl" % OS.get_process_id()
	var prepared := _prepare_record_path(requested_path)
	if not str(prepared.get("error", "")).is_empty():
		return {"ok": false, "error": str(prepared.error)}
	var path := str(prepared.path)
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return {"ok": false, "error": "open_%d" % FileAccess.get_open_error()}
	file.store_line(JSON.stringify({"kind": "lag04_record_probe", "ok": true}))
	file.close()
	var contents := FileAccess.get_file_as_string(path).strip_edges()
	var remove_error := DirAccess.remove_absolute(path)
	var write_ok := contents == JSON.stringify({"kind": "lag04_record_probe", "ok": true})
	return {"ok": write_ok and remove_error == OK, "readbackOk": write_ok, "cleanupOk": remove_error == OK}


func _prepare_record_path(requested_path: String) -> Dictionary:
	var resolved_path := requested_path
	if requested_path.begins_with("res://") or requested_path.begins_with("user://"):
		resolved_path = ProjectSettings.globalize_path(requested_path)
	elif not requested_path.is_absolute_path():
		resolved_path = ProjectSettings.globalize_path("res://" + requested_path)
	var directory_path := resolved_path.get_base_dir()
	var directory_error := DirAccess.make_dir_recursive_absolute(directory_path)
	if directory_error != OK and directory_error != ERR_ALREADY_EXISTS:
		return {"error": "cannot_create_parent_%d:%s" % [directory_error, directory_path]}
	var probe_path := resolved_path + ".lag04-write-probe-%d" % OS.get_process_id()
	var probe := FileAccess.open(probe_path, FileAccess.WRITE)
	if probe == null:
		return {"error": "cannot_write_probe_%d:%s" % [FileAccess.get_open_error(), probe_path]}
	probe.close()
	var remove_error := DirAccess.remove_absolute(probe_path)
	if remove_error != OK:
		return {"error": "cannot_remove_probe_%d:%s" % [remove_error, probe_path]}
	return {"path": resolved_path}


func _materialize_scenario(name: String, options: Dictionary, duration_ms: int) -> Dictionary:
	var result: Dictionary = SCENARIO_DEFINITIONS[name].duplicate(true)
	result["name"] = name
	result["duration_ms"] = duration_ms
	result["duration_defaulted"] = int(options.get("duration_ms", -1)) <= 0
	if int(options.get("seed", -1)) > 0:
		result["seed"] = int(options.seed)
	result["directions"] = [
		{"latency_ms": float(result.latency_ms), "jitter_ms": float(result.jitter_ms)},
		{"latency_ms": float(result.latency_ms), "jitter_ms": float(result.jitter_ms)},
	]
	result["costs"] = _costs_for_mode(str(result.cost_mode))
	result["controlOnly"] = bool(result.get("fixed_skip", false))
	return result


func _costs_for_mode(mode: String) -> Array[Dictionary]:
	var p1_fast := _fast_costs()
	var p1_slow := _slow_costs()
	var p2_fast := _fast_costs()
	return [p1_slow if mode == "slow_host" else p1_fast, p2_fast]


func _fast_costs() -> Dictionary:
	return {
		"advance_us": 5_260,
		"replay_advance_us": 5_260,
		"save_us": 9_458,
		"load_us": 0,
		"rebuild_us": 0,
		"validate_us": 0,
		"copy_us": 0,
		"provenance": "P2 simulation_step minus measured checkpoint encode+pack; replay and restore were not observed",
		"status": "provisional_estimate",
	}


func _slow_costs() -> Dictionary:
	return {
		"advance_us": 9_979,
		"replay_advance_us": 9_979,
		"save_us": 20_543,
		"load_us": 22_071,
		"rebuild_us": 0,
		"validate_us": 0,
		"copy_us": 0,
		"provenance": "P1 simulation_step minus measured checkpoint encode+pack; load_us is the estimated unsplit correction residual per load, including unknown presentation rebuilds",
		"status": "provisional_estimate",
	}


func _run_scenario(scenario: Dictionary) -> Dictionary:
	var setup := _scenario_setup(int(scenario.seed))
	var hub = PairFixture.FakeHub.new(setup)
	var first_container := Node.new()
	var second_container := Node.new()
	root.add_child(first_container)
	root.add_child(second_container)
	var first_game := _create_game(first_container, int(scenario.seed))
	var second_game := _create_game(second_container, int(scenario.seed))
	var first_room = PairFixture.FakeRoom.new()
	var first_transport = PairFixture.FakeTransport.new()
	var second_room = PairFixture.FakeRoom.new()
	var second_transport = PairFixture.FakeTransport.new()
	first_room.configure(hub, 0)
	first_transport.hub = hub
	second_room.configure(hub, 1)
	second_transport.hub = hub
	root.add_child(first_room)
	root.add_child(first_transport)
	root.add_child(second_room)
	root.add_child(second_transport)
	var first_match = Coordinator.new()
	var second_match = Coordinator.new()
	for coordinator in [first_match, second_match]:
		coordinator.sparse_saves = OS.get_cmdline_user_args().has("--sparse")
		coordinator.checkpoint_stride = 2 if OS.get_cmdline_user_args().has("--stride-two") else 1
		coordinator.host_pacing = OS.get_cmdline_user_args().has("--pacing")
	var first_error: String = first_match.configure(first_game, setup, "p1", first_room, first_transport)
	var second_error: String = second_match.configure(second_game, setup, "p2", second_room, second_transport)
	if not first_error.is_empty() or not second_error.is_empty():
		var setup_failure := _failure(scenario, "configure", {"p1": first_error, "p2": second_error})
		_dispose_pair([first_match, second_match], [first_room, second_room], [first_transport, second_transport],
			[first_game, second_game], [first_container, second_container])
		return setup_failure
	var initial_hashes := [State.fingerprint(first_match.save_state()), State.fingerprint(second_match.save_state())]
	if initial_hashes[0] != initial_hashes[1]:
		var initial_failure := _failure(scenario, "initial_state_mismatch", {"p1": initial_hashes[0], "p2": initial_hashes[1]})
		_dispose_pair([first_match, second_match], [first_room, second_room], [first_transport, second_transport],
			[first_game, second_game], [first_container, second_container])
		return initial_failure
	var start_results := {}
	_launch_start.call_deferred(first_match, setup.profile, start_results, "p1", hub.epoch)
	_launch_start.call_deferred(second_match, setup.profile, start_results, "p2", hub.epoch)
	for _attempt in 600:
		if start_results.get("p1_done", false) and start_results.get("p2_done", false):
			break
		await process_frame
	if not start_results.get("p1_done", false) or not start_results.get("p2_done", false) \
		or not str(start_results.get("p1", "startup incomplete")).is_empty() \
		or not str(start_results.get("p2", "startup incomplete")).is_empty():
		var start_failure := _failure(scenario, "start", start_results)
		_dispose_pair([first_match, second_match], [first_room, second_room], [first_transport, second_transport],
			[first_game, second_game], [first_container, second_container])
		return start_failure
	if not first_match.running or not second_match.running:
		var running_failure := _failure(scenario, "start_barrier", {"p1_running": first_match.running, "p2_running": second_match.running})
		_dispose_pair([first_match, second_match], [first_room, second_room], [first_transport, second_transport],
			[first_game, second_game], [first_container, second_container])
		return running_failure

	var network := VirtualNetwork.new(hub, scenario)
	hub.peer_router = Callable(network, "send_from_peer")
	var coordinators: Array = [first_match, second_match]
	var transports: Array = [first_transport, second_transport]
	var before_profiles: Array[Dictionary] = [_profile_counters(first_match), _profile_counters(second_match)]
	var profile_ready := bool(before_profiles[0].get("available", false)) and bool(before_profiles[1].get("available", false))
	var tape := _load_input_tape()
	if tape.is_empty() or not profile_ready:
		var prerequisite_failure := _failure(scenario, "lag02_prerequisite", {
			"profile": [before_profiles[0], before_profiles[1]],
			"input_tape_available": not tape.is_empty(),
		})
		_dispose_pair(coordinators, [first_room, second_room], transports,
			[first_game, second_game], [first_container, second_container])
		return prerequisite_failure

	var duration_ms := float(scenario.duration_ms)
	var virtual_origin_ms := Time.get_ticks_msec()
	var next_tick_ms := [0.0, 0.0]
	var busy_until_ms := [0.0, 0.0]
	var caller_ticks := [0, 0]
	var skipped_ticks := [0, 0]
	var merged_ticks := [0, 0]
	var virtual_work_us := [0, 0]
	var work_by_peer := [{}, {}]
	var seeded_inputs := _build_seeded_inputs(int(ceil(duration_ms / FRAME_INTERVAL_MS)) + 256, int(scenario.seed))
	var fatal_error := ""
	while true:
		var fire0: float = maxf(float(next_tick_ms[0]), float(busy_until_ms[0]))
		var fire1: float = maxf(float(next_tick_ms[1]), float(busy_until_ms[1]))
		var slot := 0 if fire0 <= fire1 else 1
		var fire_at_ms: float = fire0 if slot == 0 else fire1
		if fire_at_ms > duration_ms:
			break
		var due_tick: float = float(next_tick_ms[slot])
		var nominal_tick_index := int(round(due_tick / FRAME_INTERVAL_MS))
		if slot == 0 and bool(scenario.get("fixed_skip", false)) and nominal_tick_index % 6 == 5:
			skipped_ticks[slot] = int(skipped_ticks[slot]) + 1
			next_tick_ms[slot] = due_tick + FRAME_INTERVAL_MS
			continue

		network.now_ms = fire_at_ms
		var profile_before: Dictionary = _profile_counters(coordinators[slot])
		transports[slot].begin_virtual_drain()
		var messages_delivered: int = network.drain_for_peer(slot, fire_at_ms)
		transports[slot].end_virtual_drain(messages_delivered)
		var input_state := _input_for(slot, coordinators[slot], tape, seeded_inputs)
		var process_now_ms := int(floor(virtual_origin_ms + fire_at_ms))
		var tick_error: String = coordinators[slot].process_tick(process_now_ms, input_state)
		var profile_after: Dictionary = _profile_counters(coordinators[slot])
		var delta_result := _profile_delta(profile_before, profile_after)
		if not bool(delta_result.get("available", false)):
			fatal_error = "profile_delta_unavailable_p%d: %s" % [slot + 1, str(delta_result)]
			break
		var delta: Dictionary = delta_result.delta
		var peer_cost := _work_cost(delta, scenario.costs[slot])
		if not bool(peer_cost.get("available", false)):
			fatal_error = "invalid_work_cost_p%d: %s" % [slot + 1, str(peer_cost)]
			break
		var work_us := int(peer_cost.total_us)
		virtual_work_us[slot] = int(virtual_work_us[slot]) + work_us
		work_by_peer[slot] = _sum_work_breakdown(work_by_peer[slot], peer_cost.by_kind)
		var tick_start_ms := fire_at_ms
		busy_until_ms[slot] = maxf(tick_start_ms, float(busy_until_ms[slot])) + float(work_us) / 1000.0
		caller_ticks[slot] = int(caller_ticks[slot]) + 1
		var following_tick := due_tick + FRAME_INTERVAL_MS
		while following_tick <= tick_start_ms + 0.0001:
			following_tick += FRAME_INTERVAL_MS
			merged_ticks[slot] = int(merged_ticks[slot]) + 1
		next_tick_ms[slot] = following_tick
		if not tick_error.is_empty():
			fatal_error = "p%d_process_tick: %s" % [slot + 1, tick_error]
			break
		if not str(coordinators[slot].error).is_empty():
			fatal_error = "p%d_match_error: %s" % [slot + 1, str(coordinators[slot].error)]
			break
	if not fatal_error.is_empty():
		var sim_failure := _failure(scenario, "simulation", {
			"error": fatal_error,
			"caller_ticks": caller_ticks,
			"skipped_ticks": skipped_ticks,
		})
		_dispose_pair(coordinators, [first_room, second_room], transports,
			[first_game, second_game], [first_container, second_container])
		return sim_failure

	var virtual_end_ms := int(floor(virtual_origin_ms + duration_ms))
	var performance := [
		coordinators[0].call("_collect_performance_summary", virtual_end_ms, true),
		coordinators[1].call("_collect_performance_summary", virtual_end_ms, true),
	]
	var hash_comparison := _compare_hashes(network.peer_hashes)
	var profile_after_run := [_profile_counters(coordinators[0]), _profile_counters(coordinators[1])]
	var profiles_final := [
		_profile_delta(before_profiles[0], profile_after_run[0]),
		_profile_delta(before_profiles[1], profile_after_run[1]),
	]
	var virtual_result := {
		"durationMs": int(duration_ms),
		"callerTicks": caller_ticks,
		"ticksMergedDuringBusy": merged_ticks,
		"fixedSkippedTicks": skipped_ticks,
		"frontier": [int(coordinators[0].rollback.frontier), int(coordinators[1].rollback.frontier)],
		"confirmed": [int(coordinators[0].rollback.confirmed), int(coordinators[1].rollback.confirmed)],
		"logicalRateHz": [
			float(coordinators[0].rollback.frontier) * 1000.0 / duration_ms,
			float(coordinators[1].rollback.frontier) * 1000.0 / duration_ms,
		],
		"busyWorkMs": [float(virtual_work_us[0]) / 1000.0, float(virtual_work_us[1]) / 1000.0],
		"busyUntilMs": busy_until_ms,
		"workCostUsByKind": work_by_peer,
	}
	var network_summary: Dictionary = network.summary()
	var enough_common_hashes := int(hash_comparison.get("commonFrameCount", 0)) >= MIN_COMMON_HASHES
	var field_calibration := _field_calibration(scenario, performance, virtual_result)
	var ok := bool(hash_comparison.get("allEqual", false)) and enough_common_hashes \
		and bool(network_summary.get("reliableConservation", false)) \
		and bool(network_summary.get("reliableOrderVerified", false))
	var result := {
		"kind": "online_lag_simulation",
		"scenario": scenario.name,
		"seed": int(scenario.seed),
		"inputScript": {
			"fieldTape": "tests/rollback_performance_user_log_r01.json",
			"fieldTapeSourceSha256": str(tape.get("source", {}).get("sha256", "")),
			"varyingPeerSeed": int(scenario.seed),
			"varyingPeer": "seeded logical input sequence",
		},
		"clock": {
			"kind": "virtual_ms",
			"originMonotonicMs": int(virtual_origin_ms),
			"durationMs": int(duration_ms),
			"originUse": "monotonic origin only; compare deterministic runs after removing this field and wall-clock profile timings",
		},
		"network": network_summary,
		"costModel": {
			"status": "provisional_estimate",
			"sourceLogs": FIELD_LOGS,
			"unit": "microseconds per cumulative profile operation count; adjacent samples are differenced before costing",
			"costsUsPerWorkUnit": scenario.costs,
			"accounting": "advance and replay_advance are exclusive adapter.advance calls; every save_state is charged once from save_count, including replay saves; load_count and rebuild_count use separate units",
			"unmeasured": "validate/copy are observed in profile counts but have zero separate weight because legacy simulation_step already includes them; P1 load_us is a blended per-load correction residual including unseparated rebuild work, and rebuild_us stays zero",
			"busyApproximation": "all messages sent within one drain+process_tick receive that tick's fire time; measured work is charged after process_tick, so intra-callback CPU time does not delay individual sends; later caller ticks merge while busy",
			"virtualBusyWorkUs": virtual_work_us,
		},
		"virtual": virtual_result,
		"lag02ProfileDelta": profiles_final,
		"onlinePerformance": performance,
		"hashes": hash_comparison,
		"fieldCalibration": field_calibration,
		"acceptance": {
			"minimumCommonHashes": MIN_COMMON_HASHES,
			"enoughCommonHashes": enough_common_hashes,
			"commonHashesEqual": bool(hash_comparison.get("allEqual", false)),
			"reliableConservedAndOrdered": bool(network_summary.get("reliableConservation", false))
				and bool(network_summary.get("reliableOrderVerified", false)),
		},
		"ok": ok,
	}
	if bool(scenario.get("fixed_skip", false)):
		result["acceptanceUse"] = "control_only; do not use as optimization evidence"
	if not ok:
		result["failure"] = "hash mismatch, insufficient common confirmed hashes, or reliable delivery invariant failed"
	_dispose_pair(coordinators, [first_room, second_room], transports,
		[first_game, second_game], [first_container, second_container])
	return result


func _field_calibration(scenario: Dictionary, performance: Array, virtual_result: Dictionary) -> Dictionary:
	if str(scenario.get("name", "")) != "turn40-slowhost":
		return {"status": "not_applicable", "calibrated": false}
	var p1: Dictionary = performance[0]
	var p2: Dictionary = performance[1]
	var p1_totals: Dictionary = p1.get("matchTotals", {})
	var p2_totals: Dictionary = p2.get("matchTotals", {})
	var p1_waits: Dictionary = p1_totals.get("waitMs", {})
	var p2_waits: Dictionary = p2_totals.get("waitMs", {})
	var host_corrections := int(p1_totals.get("correctionCount", 0))
	var guest_corrections := int(p2_totals.get("correctionCount", 0))
	var host_input_wait_ms := int(p1_waits.get("input", 0))
	var guest_clock_wait_ms := int(p2_waits.get("clock", 0))
	return {
		"status": "provisional_not_calibrated",
		"calibrated": false,
		"reason": "legacy logs do not split load from presentation rebuild, so these provisional weights cannot pass field calibration",
		"fieldReferenceHz": {"p1": 14.107, "p2": 14.045},
		"observedLogicalRateHz": virtual_result.get("logicalRateHz", []),
		"hostCorrections": host_corrections,
		"guestCorrections": guest_corrections,
		"hostInputWaitMs": host_input_wait_ms,
		"guestClockWaitMs": guest_clock_wait_ms,
		"correctionWaitPatternObserved": host_corrections > 0 and guest_corrections == 0
			and host_input_wait_ms > 0 and guest_clock_wait_ms > 0,
		"waitDeltaMs": abs(host_input_wait_ms - guest_clock_wait_ms),
	}


func _network_semantics_smoke() -> Dictionary:
	var reliable_seed := -1
	var unordered_seed := -1
	var loss_seed := -1
	for candidate_seed in range(1, 4096):
		var jitter_config := _probe_network_config(candidate_seed, 0.0, 20.0)
		jitter_config.loss_rate = 1.0
		var reliable_recorder := PacketRecorder.new()
		var jitter_probe := VirtualNetwork.new(reliable_recorder, jitter_config)
		jitter_probe.send_from_peer(0, _probe_message("reliable", 1))
		jitter_probe.send_from_peer(0, _probe_message("reliable", 2))
		var sampled_out_of_order := float(jitter_probe.pending[1].sampled_arrival_ms) \
			< float(jitter_probe.pending[0].sampled_arrival_ms)
		var arrivals_ordered := float(jitter_probe.pending[0].arrival_ms) \
			<= float(jitter_probe.pending[1].arrival_ms)
		var reliable_ready_at := maxf(float(jitter_probe.pending[0].arrival_ms), float(jitter_probe.pending[1].arrival_ms))
		jitter_probe.drain_for_peer(1, reliable_ready_at + 0.01)
		var reliable_stats: Dictionary = jitter_probe.summary()
		if sampled_out_of_order and arrivals_ordered \
			and int(reliable_stats.lostByChannel.reliable) == 0 \
			and int(reliable_stats.reliableOrderViolations) == 0 \
			and reliable_recorder.delivered.size() == 2 \
			and int(reliable_recorder.delivered[0].envelope.seq) == 1 \
			and int(reliable_recorder.delivered[1].envelope.seq) == 2:
			reliable_seed = candidate_seed
			break
	for candidate_seed in range(1, 4096):
		var jitter_config := _probe_network_config(candidate_seed, 0.0, 20.0)
		var unordered_recorder := PacketRecorder.new()
		var jitter_probe := VirtualNetwork.new(unordered_recorder, jitter_config)
		jitter_probe.send_from_peer(0, _probe_message("input", 1))
		jitter_probe.send_from_peer(0, _probe_message("input", 2))
		if jitter_probe.pending.size() == 2 \
			and float(jitter_probe.pending[1].arrival_ms) < float(jitter_probe.pending[0].arrival_ms):
			var ready_at := maxf(float(jitter_probe.pending[0].arrival_ms), float(jitter_probe.pending[1].arrival_ms))
			jitter_probe.drain_for_peer(1, ready_at + 0.01)
			var unordered_stats: Dictionary = jitter_probe.summary()
			if unordered_recorder.delivered.size() == 2 \
				and int(unordered_recorder.delivered[0].envelope.seq) == 2 \
				and int(unordered_stats.reorderedUnordered) == 1:
				unordered_seed = candidate_seed
				break
	for candidate_seed in range(1, 4096):
		var loss_config := _probe_network_config(candidate_seed, 0.5, 0.0)
		var loss_recorder := PacketRecorder.new()
		var loss_probe := VirtualNetwork.new(loss_recorder, loss_config)
		loss_probe.send_from_peer(0, _probe_message("input", 1))
		loss_probe.send_from_peer(0, _probe_message("input", 2))
		if int(loss_probe.summary().lost) == 1 and loss_probe.pending.size() == 1 \
			and int(loss_probe.pending[0].sequence) == 2:
			loss_probe.drain_for_peer(1, float(loss_probe.pending[0].arrival_ms) + 0.01)
			var loss_stats: Dictionary = loss_probe.summary()
			if loss_recorder.delivered.size() == 1 \
				and int(loss_recorder.delivered[0].envelope.seq) == 2 \
				and int(loss_stats.lostByChannel.input) == 1:
				loss_seed = candidate_seed
				break
	var all_passed := reliable_seed >= 0 and unordered_seed >= 0 and loss_seed >= 0
	return {
		"kind": "online_lag_network_self_test",
		"reliableNeverLostAndOrderedUnderInvertedJitter": reliable_seed >= 0,
		"unorderedCanReorder": unordered_seed >= 0,
		"unorderedLossDoesNotBlockNextPacket": loss_seed >= 0,
		"seeds": {"reliable": reliable_seed, "unordered": unordered_seed, "loss": loss_seed},
		"ok": all_passed,
	}


func _probe_network_config(seed: int, loss_rate: float, jitter_ms: float) -> Dictionary:
	return {
		"seed": seed,
		"loss_rate": loss_rate,
		"latency_ms": 5.0,
		"jitter_ms": jitter_ms,
		"directions": [
			{"latency_ms": 5.0, "jitter_ms": jitter_ms},
			{"latency_ms": 5.0, "jitter_ms": jitter_ms},
		],
	}


func _probe_message(channel: String, sequence: int) -> Dictionary:
	return {"channel": channel, "envelope": {"seq": sequence, "type": "probe", "payload": {}}}


func _profile_counters(coordinator: Object) -> Dictionary:
	var session: Variant = coordinator.get("rollback")
	if not session is Object or not session.has_method("profile_counters"):
		return {"available": false, "reason": "rollback_profile_counters_unavailable"}
	var value: Variant = session.call("profile_counters")
	if not value is Dictionary:
		return {"available": false, "reason": "rollback_profile_counters_invalid"}
	var wrapped := {"available": true}
	for key in value:
		wrapped[key] = value[key]
	return wrapped


func _profile_delta(before: Dictionary, after: Dictionary) -> Dictionary:
	if not bool(before.get("available", true)) or not bool(after.get("available", true)):
		return {"available": false, "reason": "profile_counter_unavailable", "before": before, "after": after}
	var delta := {}
	for key in after:
		if key == "available" or key == "reason":
			continue
		var current: Variant = after[key]
		if not current is int and not current is float:
			continue
		var previous_value: Variant = before.get(key, 0)
		if not previous_value is int and not previous_value is float:
			return {"available": false, "reason": "profile_counter_type_changed", "key": str(key)}
		var difference := int(current) - int(previous_value)
		if difference < 0:
			return {"available": false, "reason": "profile_counter_decreased", "key": str(key)}
		delta[key] = difference
	return {"available": true, "delta": delta}


func _work_cost(delta: Dictionary, weights: Dictionary) -> Dictionary:
	var replay_saves := int(delta.get("replay_save_count", 0))
	var saves := int(delta.get("save_count", 0))
	if replay_saves < 0 or replay_saves > saves:
		return {"available": false, "reason": "replay_save_count_not_a_subset", "saves": saves, "replay_saves": replay_saves}
	var categories := {
		"advance": int(delta.get("advance_count", 0)) * int(weights.get("advance_us", 0)),
		"replay_advance": int(delta.get("replay_advance_count", 0)) * int(weights.get("replay_advance_us", 0)),
		"save": saves * int(weights.get("save_us", 0)),
		"load": int(delta.get("load_count", 0)) * int(weights.get("load_us", 0)),
		"rebuild": int(delta.get("rebuild_count", 0)) * int(weights.get("rebuild_us", 0)),
		"validate": int(delta.get("validate_count", 0)) * int(weights.get("validate_us", 0)),
		"copy": int(delta.get("copy_count", 0)) * int(weights.get("copy_us", 0)),
	}
	var total := 0
	for amount in categories.values():
		total += int(amount)
	return {"available": true, "total_us": total, "by_kind": categories}


func _sum_work_breakdown(total: Dictionary, increment: Dictionary) -> Dictionary:
	var result: Dictionary = total.duplicate(true)
	for key in increment:
		result[key] = int(result.get(key, 0)) + int(increment[key])
	return result


func _compare_hashes(peer_hashes: Array) -> Dictionary:
	var left: Dictionary = peer_hashes[0]
	var right: Dictionary = peer_hashes[1]
	var left_frames: Array[int] = []
	var right_frames: Array[int] = []
	var common_frames: Array[int] = []
	var p1_only_frames: Array[int] = []
	var p2_only_frames: Array[int] = []
	for frame in left:
		left_frames.append(int(frame))
		if right.has(frame):
			common_frames.append(int(frame))
		else:
			p1_only_frames.append(int(frame))
	for frame in right:
		right_frames.append(int(frame))
		if not left.has(frame):
			p2_only_frames.append(int(frame))
	left_frames.sort()
	right_frames.sort()
	common_frames.sort()
	p1_only_frames.sort()
	p2_only_frames.sort()
	var comparisons: Array[Dictionary] = []
	var all_equal := not common_frames.is_empty()
	for frame in common_frames:
		var left_hash := str(left.get(frame, ""))
		var right_hash := str(right.get(frame, ""))
		var equal := not left_hash.is_empty() and left_hash == right_hash
		all_equal = all_equal and equal
		comparisons.append({"frame": frame, "p1": left_hash, "p2": right_hash, "equal": equal})
	var common_range: Variant = [common_frames[0], common_frames[-1]] if not common_frames.is_empty() else null
	return {
		"interval": 30,
		"byFrame": comparisons,
		"commonFrameCount": common_frames.size(),
		"commonConfirmedFrameRange": common_range,
		"p1HashFrameCount": left_frames.size(),
		"p2HashFrameCount": right_frames.size(),
		"pendingOneSidedFrames": {"p1": p1_only_frames, "p2": p2_only_frames},
		"allEqual": all_equal,
	}


func _load_input_tape() -> Dictionary:
	var contents := FileAccess.get_file_as_string(TAPE_PATH)
	if contents.is_empty():
		return {}
	var parsed: Variant = JSON.parse_string(contents)
	return parsed if parsed is Dictionary and parsed.get("records") is Array else {}


func _build_seeded_inputs(frame_count: int, seed: int) -> Array[Dictionary]:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var result: Array[Dictionary] = []
	var held := _neutral_input()
	for frame in range(frame_count):
		if frame % 5 == 0:
			held = _neutral_input()
			if rng.randf() < 0.55:
				held["right" if rng.randf() < 0.5 else "left"] = true
			if rng.randf() < 0.14:
				held["attack"] = true
			if rng.randf() < 0.08:
				held["ranged"] = true
			if rng.randf() < 0.05:
				held["jump"] = true
		result.append(held.duplicate())
	return result


func _input_for(slot: int, coordinator: Object, tape: Dictionary, seeded: Array[Dictionary]) -> Dictionary:
	var frame := int(coordinator.rollback.frontier) + 1
	if slot == 0:
		var records: Array = tape.get("records", [])
		var index := frame - 1
		if index >= 0 and index < records.size() and records[index] is Dictionary:
			var held: Variant = records[index].get("p1")
			if held is Dictionary:
				return held.duplicate(true)
			return _neutral_input()
	var seeded_index := frame - 1
	return seeded[seeded_index].duplicate() if seeded_index >= 0 and seeded_index < seeded.size() else _neutral_input()


func _scenario_setup(seed: int) -> Dictionary:
	var network_profile: Dictionary = DEFAULT_PROFILE.duplicate(true)
	for argument in OS.get_cmdline_user_args():
		if argument == "--online-window=0": network_profile.predictionWindow = 0
		if argument in ["--online-delay=3", "--online-delay=4"]:
			network_profile.inputDelay = int(argument.get_slice("=", 1))
	network_profile.id = "chrome-exp-d%d-p%d" % [network_profile.inputDelay, network_profile.predictionWindow]
	return {
		"members": [
			{"choice": {"fighter": "minren", "helper": "woailuo"}},
			{"choice": {"fighter": "yihu", "helper": "kon"}},
		],
		"stage": "现世",
		"rules": {"time": 100, "life": 5},
		"seed": seed,
		"profile": network_profile,
	}


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


func _launch_start(coordinator: Object, profile: Dictionary, results: Dictionary, slot: String, match_epoch: String) -> void:
	var start_error: String = await coordinator.start(match_epoch, profile, "p1")
	results[slot] = start_error
	results[slot + "_done"] = true


func _dispose_pair(coordinators: Array, rooms: Array, transports: Array, games: Array, containers: Array) -> void:
	for coordinator in coordinators:
		if coordinator is Object and is_instance_valid(coordinator):
			coordinator.close()
	for dependency in rooms + transports:
		if dependency is Object and is_instance_valid(dependency):
			dependency.free()
	for game in games:
		if game is Object and is_instance_valid(game):
			game._goto_menu()
			game.free()
	for container in containers:
		if container is Object and is_instance_valid(container):
			container.free()


func _failure(scenario: Dictionary, stage: String, details: Variant) -> Dictionary:
	return {
		"kind": "online_lag_simulation",
		"scenario": str(scenario.get("name", "unknown")),
		"seed": int(scenario.get("seed", 0)),
		"stage": stage,
		"details": details,
		"ok": false,
	}


func _neutral_input() -> Dictionary:
	var held := {}
	for button in BUTTONS:
		held[button] = false
	return held
