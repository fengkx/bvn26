extends SceneTree

const Rollback = preload("res://rollback_session.gd")
const State = preload("res://simulation_state.gd")
const InputSource = preload("res://keyboard_input_source.gd")
const PHYSICS_HZ := 30
const MEASURED_SECONDS := 60
const DRAIN_TICKS := 120
const EPOCH := "turn-buffer-model"
const PROFILES := [
	{"id": "d0p2", "inputDelay": 0, "predictionWindow": 2},
	{"id": "d1p4", "inputDelay": 1, "predictionWindow": 4},
	{"id": "d2p6", "inputDelay": 2, "predictionWindow": 6},
]
const RTT_CASES := [50, 100, 150]
const JITTER_MS := [-8, 0, 8, 4, -4, 0, 8, -8, 4, 0, -4, 8]


class SimAdapter extends RefCounted:
	const SimState = preload("res://simulation_state.gd")
	const SimInput = preload("res://keyboard_input_source.gd")
	const Build := "turn-buffer-model-v1"
	var frame := 0
	var counters: Dictionary = {}

	func _init() -> void:
		for slot in ["p1", "p2"]:
			counters[slot] = {}
			for button in SimInput.BUTTONS:
				counters[slot][button] = 0

	func save_state() -> Dictionary:
		return SimState.pack_state(Build, frame, {"state_frame": frame, "counters": counters})

	func validate_state(snapshot: Dictionary) -> String:
		var problem := SimState.validate_snapshot(snapshot, Build, ["state_frame", "counters"])
		if not problem.is_empty():
			return problem
		if not snapshot.owners.get("state_frame") is int or int(snapshot.owners.state_frame) != int(snapshot.frame):
			return "Adapter frame mismatch"
		for slot in ["p1", "p2"]:
			if not snapshot.owners.counters.get(slot) is Dictionary:
				return "Missing counter slot: " + slot
		return ""

	func load_state(snapshot: Dictionary) -> String:
		var problem := SimState.validate_snapshot(snapshot, Build, ["state_frame", "counters"])
		if not problem.is_empty():
			return problem
		frame = int(snapshot.frame)
		counters = snapshot.owners.counters.duplicate(true)
		return ""

	func advance(next_frame: int, players: Dictionary) -> String:
		if next_frame != frame + 1:
			return "Non-contiguous synthetic frame"
		for slot in ["p1", "p2"]:
			var held: Dictionary = players[slot]
			for button in SimInput.BUTTONS:
				if bool(held[button]):
					counters[slot][button] = int(counters[slot][button]) + 1
		frame = next_frame
		return ""


class ReliableWire extends RefCounted:
	const JITTER := [-8, 0, 8, 4, -4, 0, 8, -8, 4, 0, -4, 8]
	var rtt_ms: int
	var queues: Array = [[], []]
	var last_delivery_ms: Array[float] = [-1.0, -1.0]
	var sequences: Array[int] = [0, 0]
	var sent_count: Array[int] = [0, 0]

	func _init(rtt: int) -> void:
		rtt_ms = rtt

	func send(from_slot: int, kind: String, payload: Dictionary, now_ms: float) -> void:
		sequences[from_slot] += 1
		sent_count[from_slot] += 1
		var jitter: int = JITTER[(sequences[from_slot] - 1) % JITTER.size()]
		var one_way := maxf(0.0, float(rtt_ms) / 2.0 + float(jitter))
		var due_ms := maxf(last_delivery_ms[from_slot], now_ms + one_way)
		last_delivery_ms[from_slot] = due_ms
		queues[1 - from_slot].append({
			"seq": sequences[from_slot], "kind": kind, "payload": payload.duplicate(true),
			"due_ms": due_ms, "from": from_slot,
		})

	func take_due(to_slot: int, now_ms: float) -> Array[Dictionary]:
		var due: Array[Dictionary] = []
		var waiting: Array[Dictionary] = []
		for packet in queues[to_slot]:
			if float(packet.due_ms) <= now_ms:
				due.append(packet)
			else:
				waiting.append(packet)
		queues[to_slot] = waiting
		return due

	func pending_count() -> int:
		return queues[0].size() + queues[1].size()


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var results: Array[Dictionary] = []
	for rtt in RTT_CASES:
		for profile in PROFILES:
			var result := _run_case(int(rtt), profile)
			results.append(result)
			print("TURN_BUFFER_CASE ", JSON.stringify(result))
	print("TURN_BUFFER_MODEL_COMPLETE cases=%d measured_seconds=%d rtt_ms=%s jitter_ms=%s" % [
		results.size(), MEASURED_SECONDS, str(RTT_CASES), str(JITTER_MS),
	])
	quit()


func _run_case(rtt_ms: int, profile: Dictionary) -> Dictionary:
	var wire := ReliableWire.new(rtt_ms)
	var peers: Array[Dictionary] = []
	for slot in ["p1", "p2"]:
		var adapter := SimAdapter.new()
		var session := Rollback.new()
		var delay := int(profile.inputDelay)
		var window := int(profile.predictionWindow)
		var setup_error: String = session.configure(adapter, EPOCH, window, maxi(32, window + delay + 8), delay)
		assert(setup_error.is_empty(), setup_error)
		peers.append({
			"slot": slot, "index": 0 if slot == "p1" else 1, "adapter": adapter, "session": session,
			"sampled_frontier": -1, "sampled_held": {}, "clock_samples": {},
			"clock_origin_ms": -1.0, "wait_ticks": 0, "input_wait_ticks": 0,
			"clock_wait_ticks": 0, "corrections": 0, "replayed_frames": 0,
			"received_inputs": 0, "received_clock": 0,
		})
	var windows: Array[Dictionary] = []
	var previous_frontier := [0, 0]
	var tick_count := MEASURED_SECONDS * PHYSICS_HZ
	for tick in tick_count:
		var now_ms: float = floorf(float(tick) * 1000.0 / float(PHYSICS_HZ))
		_process_peer_tick(peers[0], peers[1], wire, now_ms, tick)
		_process_peer_tick(peers[1], peers[0], wire, now_ms, tick)
		if (tick + 1) % (10 * PHYSICS_HZ) == 0:
			var current_frontier := [int(peers[0].session.frontier), int(peers[1].session.frontier)]
			windows.append({
				"seconds": (tick + 1) / PHYSICS_HZ,
				"p1_advanced": current_frontier[0] - previous_frontier[0],
				"p2_advanced": current_frontier[1] - previous_frontier[1],
				"p1_frontier": current_frontier[0], "p2_frontier": current_frontier[1],
				"p1_confirmed": int(peers[0].session.confirmed),
				"p2_confirmed": int(peers[1].session.confirmed),
			})
			previous_frontier = current_frontier
		var problem := str(peers[0].session.error) + str(peers[1].session.error)
		if not problem.is_empty():
			return {"profile": profile.id, "rttMs": rtt_ms, "error": problem, "tick": tick}

	var measured: Array[Dictionary] = []
	for peer in peers:
		measured.append({
			"frontier": int(peer.session.frontier), "confirmed": int(peer.session.confirmed),
			"wait_ticks": int(peer.wait_ticks), "input_wait_ticks": int(peer.input_wait_ticks),
			"clock_wait_ticks": int(peer.clock_wait_ticks), "corrections": int(peer.corrections),
			"replayed_frames": int(peer.replayed_frames),
		})

	# Stop taking new local input samples, then continue host/guest ticks so the
	# already sampled inputs, authoritative clocks and corrections can converge.
	# These advances are recorded separately and never contribute to the 60s rate.
	var convergence_advanced := [0, 0]
	for convergence_tick in DRAIN_TICKS:
		var tick := tick_count + convergence_tick
		var now_ms: float = floorf(float(tick) * 1000.0 / float(PHYSICS_HZ))
		var before_frontiers := [int(peers[0].session.frontier), int(peers[1].session.frontier)]
		_process_peer_tick(peers[0], peers[1], wire, now_ms, tick, false)
		_process_peer_tick(peers[1], peers[0], wire, now_ms, tick, false)
		for peer_index in [0, 1]:
			convergence_advanced[peer_index] += int(peers[peer_index].session.frontier) - before_frontiers[peer_index]
		var problem := str(peers[0].session.error) + str(peers[1].session.error)
		if not problem.is_empty():
			return {"profile": profile.id, "rttMs": rtt_ms, "error": problem, "convergenceTick": convergence_tick}
	var common_confirmed := mini(
		mini(int(peers[0].session.confirmed), int(peers[0].session.frontier)),
		mini(int(peers[1].session.confirmed), int(peers[1].session.frontier)))
	if common_confirmed <= 0:
		return {"profile": profile.id, "rttMs": rtt_ms, "error": "No common confirmed frame after convergence"}
	var p1_common: Dictionary = peers[0].session.state_at(common_confirmed)
	var p2_common: Dictionary = peers[1].session.state_at(common_confirmed)
	if p1_common.is_empty() or p2_common.is_empty():
		return {"profile": profile.id, "rttMs": rtt_ms, "error": "Common confirmed state was pruned or missing"}
	var p1_state_problem: String = peers[0].adapter.validate_state(p1_common)
	var p2_state_problem: String = peers[1].adapter.validate_state(p2_common)
	if not p1_state_problem.is_empty() or not p2_state_problem.is_empty():
		return {"profile": profile.id, "rttMs": rtt_ms, "error": "Invalid common state: %s / %s" % [p1_state_problem, p2_state_problem]}
	if int(p1_common.frame) != common_confirmed or int(p2_common.frame) != common_confirmed:
		return {"profile": profile.id, "rttMs": rtt_ms, "error": "Common state frame differs from common confirmed frame"}
	var state_difference := State.first_difference(p1_common, p2_common)
	if not state_difference.is_empty():
		return {"profile": profile.id, "rttMs": rtt_ms, "error": "Common confirmed states diverged: " + state_difference}
	var max_predicted_backlog := [0, 0]
	for peer_index in [0, 1]:
		for sample in windows:
			var backlog := int(sample["p%d_frontier" % (peer_index + 1)]) - int(sample["p%d_confirmed" % (peer_index + 1)])
			max_predicted_backlog[peer_index] = maxi(max_predicted_backlog[peer_index], backlog)
	return {
		"profile": profile.id, "inputDelayFrames": profile.inputDelay,
		"nominalInputDelayMs": float(profile.inputDelay) * 1000.0 / float(PHYSICS_HZ),
		"predictionWindowFrames": profile.predictionWindow,
		"rttMs": rtt_ms, "oneWayJitterMs": JITTER_MS,
		"virtualPhysicsTicks": tick_count, "virtualSeconds": MEASURED_SECONDS,
		"p1Frontier": measured[0].frontier, "p2Frontier": measured[1].frontier,
		"p1FrontierPerVirtualSecond": float(measured[0].frontier) / float(MEASURED_SECONDS),
		"p2FrontierPerVirtualSecond": float(measured[1].frontier) / float(MEASURED_SECONDS),
		"p1Confirmed": measured[0].confirmed, "p2Confirmed": measured[1].confirmed,
		"p1FrontierAfterConvergence": peers[0].session.frontier,
		"p2FrontierAfterConvergence": peers[1].session.frontier,
		"convergenceTicksMax": DRAIN_TICKS,
		"p1ConvergenceFramesAdvanced": convergence_advanced[0],
		"p2ConvergenceFramesAdvanced": convergence_advanced[1],
		"p1MaxSampledPredictionBacklog": max_predicted_backlog[0],
		"p2MaxSampledPredictionBacklog": max_predicted_backlog[1],
		"predictionBacklogSamplingIntervalSeconds": 10,
		"p1WaitTicks": measured[0].wait_ticks, "p2WaitTicks": measured[1].wait_ticks,
		"p1InputWaitTicks": measured[0].input_wait_ticks, "p2InputWaitTicks": measured[1].input_wait_ticks,
		"p1ClockWaitTicks": measured[0].clock_wait_ticks, "p2ClockWaitTicks": measured[1].clock_wait_ticks,
		"p1Corrections": measured[0].corrections, "p2Corrections": measured[1].corrections,
		"p1ReplayedFrames": measured[0].replayed_frames, "p2ReplayedFrames": measured[1].replayed_frames,
		"pendingPacketsAfterConvergence": wire.pending_count(),
		"commonConfirmedFrameAfterConvergence": common_confirmed,
		"commonConfirmedStateValid": true,
		"commonStateMatchesAfterConvergence": state_difference.is_empty(),
		"commonStateDifference": state_difference,
		"reliableOrdered": true, "guestClockGate": true,
		"windows10s": windows,
	}


func _process_peer_tick(peer: Dictionary, remote_peer: Dictionary, wire: ReliableWire,
		now_ms: float, physics_tick: int, allow_sampling: bool = true) -> void:
	var session = peer.session
	var slot_index := int(peer.index)
	for packet in wire.take_due(slot_index, now_ms):
		var expected_sequence := int(peer.get("last_received_sequence", 0)) + 1
		if int(packet.seq) != expected_sequence:
			session.error = "Reliable packet sequence gap: expected %d got %d" % [expected_sequence, int(packet.seq)]
			return
		peer.last_received_sequence = int(packet.seq)
		match str(packet.kind):
			"input_frame":
				var corrections_before := int(session.rollback_count)
				var replayed_before := int(session.replayed_frames)
				var problem: String = session.receive(EPOCH, str(remote_peer.slot), int(packet.payload.frame), packet.payload.held)
				if not problem.is_empty():
					session.error = "peer input rejected: " + problem
					return
				peer.received_inputs = int(peer.received_inputs) + 1
				peer.corrections = int(peer.corrections) + int(session.rollback_count) - corrections_before
				peer.replayed_frames = int(peer.replayed_frames) + int(session.replayed_frames) - replayed_before
			"clock_sample":
				var frame := int(packet.payload.frame)
				var elapsed := int(packet.payload.elapsed_ms)
				if str(peer.slot) != "p2" or not session.can_receive_frame(frame) \
					or (peer.clock_samples.has(frame) and int(peer.clock_samples[frame]) != elapsed):
					session.error = "authoritative clock sample rejected at frame %d" % frame
					return
				peer.clock_samples[frame] = elapsed
				peer.received_clock = int(peer.received_clock) + 1
			_:
				session.error = "Unexpected synthetic packet: " + str(packet.kind)
				return

	var next_frame := int(session.frontier) + 1
	if allow_sampling and int(peer.sampled_frontier) != next_frame:
		var held := _held_for(str(peer.slot), physics_tick)
		var sample: Dictionary = session.sample_local(str(peer.slot), next_frame, held)
		if sample.has("error"):
			session.error = "local sample rejected: " + str(sample.error)
			return
		peer.sampled_frontier = next_frame
		peer.sampled_held = held.duplicate(true)
		wire.send(slot_index, "input_frame", sample, now_ms)
	if str(peer.slot) == "p2" and not peer.clock_samples.has(next_frame):
		peer.wait_ticks = int(peer.wait_ticks) + 1
		peer.clock_wait_ticks = int(peer.clock_wait_ticks) + 1
		return
	var previous_frontier := int(session.frontier)
	var result: String = session.step()
	if result == "waiting_for_input":
		peer.wait_ticks = int(peer.wait_ticks) + 1
		peer.input_wait_ticks = int(peer.input_wait_ticks) + 1
		return
	if not result.is_empty() and result not in ["waiting_for_confirmation", "match_finished"]:
		session.error = result
		return
	if int(session.frontier) > previous_frontier:
		peer.sampled_frontier = -1
		peer.sampled_held.clear()
		if str(peer.slot) == "p1":
			if float(peer.clock_origin_ms) < 0.0:
				peer.clock_origin_ms = now_ms
			var elapsed_ms := maxi(0, int(now_ms - float(peer.clock_origin_ms)))
			wire.send(slot_index, "clock_sample", {"frame": session.frontier, "elapsed_ms": elapsed_ms}, now_ms)
		var oldest := int(session.oldest_frame())
		for frame in peer.clock_samples.keys():
			if int(frame) <= oldest:
				peer.clock_samples.erase(frame)


func _held_for(slot: String, physics_tick: int) -> Dictionary:
	var held := {}
	for button in InputSource.BUTTONS:
		held[button] = false
	var phase := (physics_tick + (0 if slot == "p1" else 13)) % 180
	held.attack = phase >= 9 and phase <= 11
	held.left = phase >= 40 and phase <= 69
	held.right = phase >= 110 and phase <= 129
	held.jump = phase == 82
	held.special = physics_tick % 240 == 120
	held.summon = physics_tick % 300 == 230
	return held
