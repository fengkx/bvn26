extends SceneTree
const Coordinator = preload("res://online_match.gd")
const Session = preload("res://rollback_session.gd")
const State = preload("res://simulation_state.gd")
class Adapter extends RefCounted:
	var frame := 0
	var required_frame := -1
	func must_save_frame(value: int) -> bool: return value == required_frame
	func save_state() -> Dictionary: return State.pack_state("test", frame, {"value": frame})
	func validate_state(_state: Dictionary) -> String: return ""
	func load_state(state: Dictionary) -> String:
		frame = state.frame
		return ""
	func advance(next: int, _players: Dictionary) -> String:
		frame = next
		return ""
class Peer extends Coordinator:
	var recovery_attempts := 0
	func _begin_recovery(_reason: String, _now: int) -> void:
		recovery_attempts += 1
		recovering = true
	func _abort_local(kind: String, _details: Dictionary, _notify_peer: bool = true) -> String:
		error = kind
		running = false
		return error
	func _maybe_hash_confirmed() -> void: pass
	func _maybe_finish_result() -> void: pass
class Transport extends RefCounted:
	var packets := []
	func send_peer_message(channel: String, type: String, payload: Dictionary) -> bool:
		packets.append({"channel": channel, "type": type, "payload": payload.duplicate(true)})
		return true
func _initialize() -> void:
	var peer := Peer.new()
	peer.profile = {"inputDelay": 3, "predictionWindow": 0}
	peer.local_slot = "p1"
	peer.remote_slot = "p2"
	peer.epoch = "test"
	peer.running = true
	peer._process_now_ms = 0
	peer.rollback = Session.new()
	peer.peer_transport = Transport.new()
	assert(peer.rollback.configure(Adapter.new(), "test", 0, 32, 3).is_empty())
	var held := {}
	for button in Session.BUTTONS: held[button] = false
	for i in 3:
		assert(peer._sample_local_once(held))
		peer._send_input_packet()
		assert(peer.rollback.step().is_empty())
	peer._sample_local_once(held)
	peer._send_input_packet()
	assert(peer.rollback.step() == "waiting_for_input")
	# First packets are lost. A duplicate/out-of-order tail must not ACK a gap.
	var batch := {"epoch": "test", "ack": 3, "inputs": [{"frame": 6, "held": held}]}
	peer.receive_peer_message("input", "input_batch", batch, 5)
	peer.receive_peer_message("input", "input_batch", batch, 5)
	assert(peer._remote_input_ack == 3)
	peer._process_now_ms = 123
	peer.receive_peer_message("reliable", "heartbeat", {"epoch": "test"}, 5)
	assert(peer._last_heartbeat_received_ms == 123, "Channel sequences must be independent")
	batch.inputs = [{"frame": 5, "held": held}, {"frame": 4, "held": held}]
	peer.receive_peer_message("input", "input_batch", batch, 4)
	assert(peer._remote_input_ack == 6 and peer.rollback.confirmed == 6)
	assert(peer.rollback.step().is_empty())
	batch.inputs = []
	batch.ack = 6
	peer.receive_peer_message("input", "input_batch", batch, 6)
	assert(peer._unacked_inputs.keys() == [7])
	peer._send_input_packet()
	var packet: Dictionary = peer.peer_transport.packets.back()
	assert(packet.channel == "input" and packet.payload.ack == 6)
	assert(packet.payload.inputs.size() == 1 and packet.payload.inputs[0].frame == 7)
	assert(peer.rollback.profile.save_count == 1, "Lockstep only needs its initial checkpoint before periodic/control frames")
	assert(peer.error.is_empty())
	var adapter := Adapter.new()
	adapter.required_frame = 13
	var lockstep := Session.new()
	assert(lockstep.configure(adapter, "lockstep", 0, 32).is_empty())
	for frame in range(1, 61):
		for slot in ["p1", "p2"]: assert(lockstep.receive("lockstep", slot, frame, held).is_empty())
		assert(lockstep.step().is_empty())
	assert(lockstep.profile.save_count == 4, "Keep initial, control and periodic checkpoints in lockstep")
	assert(not lockstep.state_at(30).is_empty() and not lockstep.state_at(60).is_empty())
	peer._process_now_ms = 10123
	peer._send_input_packet()
	assert(peer.recovery_attempts == 1)
	peer.recovering = false
	peer._process_now_ms = 11123
	peer._send_input_packet()
	assert(peer.recovery_attempts == 1)
	peer._process_now_ms = 17683
	peer._send_input_packet()
	assert(peer.error.is_empty(), "Background suspension must not abort input delivery")
	peer._process_now_ms = 60123
	peer._send_input_packet()
	assert(peer.error == "input_ack_timeout")
	print("ONLINE_REDUNDANT_INPUTS_SMOKE_OK loss_gap_duplicate_reorder_ack_lockstep=true")
	quit()
