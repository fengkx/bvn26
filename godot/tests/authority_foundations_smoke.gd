extends SceneTree
const Selection = preload("res://authority_host_selection.gd")
const Queue = preload("res://authority_input_queue.gd")
const Wire = preload("res://authority_wire.gd")

func report(cost: int, stalls: int = 0) -> Dictionary:
	return {"profile": Selection.PROFILE, "samples": 120, "visible": true, "p95_us": cost, "long_stalls": stalls}

func _initialize() -> void:
	assert(Selection.choose(report(850), report(1000)) == 0)
	assert(Selection.choose(report(850, 1), report(1000)) == 1)
	assert(Selection.choose(report(849, 9), report(1000)) == 0)
	assert(Selection.choose({}, {}) == -1)
	assert(Selection.choose({}, report(10)) == 1)
	var queue := Queue.new()
	var neutral := Queue.neutral()
	var attack := neutral.duplicate()
	attack.attack = true
	assert(queue.receive(2, attack, 10).is_empty())
	assert(queue.consume(20) == neutral)
	assert(queue.receive(1, neutral, 21).is_empty())
	assert(queue.consume(22) == neutral)
	assert(queue.consume(23) == attack)
	assert(queue.receive(2, neutral, 30) == "conflicting_authority_input")
	assert(queue.receive(2, attack, 240).is_empty())
	assert(queue.consume(261) == neutral)
	for i in range(3, 10): assert(queue.receive(i, neutral, 300).is_empty())
	assert(queue.pending.size() <= 4 and queue.expired > 0)
	queue.reset()
	assert(queue.receive(8, neutral, 1000).is_empty())
	assert(queue.pending.is_empty() and queue.last_received_ms == -1)
	assert(queue.consume(1001) == neutral)
	var wire := Wire.new()
	var value := {"a": [1, true, 2.5, "hello"], "b": null}
	var packet := wire.encode(value)
	assert(not packet.is_empty())
	assert(wire.decode(packet) == value)
	assert(wire.encode({"object": self}).is_empty())
	assert(wire.encode({"nan": NAN}).is_empty())
	var large := {"values": []}
	for i in 1000: large.values.append("repeatable")
	packet = wire.encode(large)
	assert(packet[0] == 1 and wire.decode(packet) == large)
	packet.encode_u32(1, Wire.MAX_RAW_BYTES + 1)
	assert(wire.decode(packet).is_empty())
	print("AUTHORITY_FOUNDATIONS_OK")
	quit()
