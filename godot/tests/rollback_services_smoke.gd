extends SceneTree

const State := preload("res://simulation_state.gd")
const Clock := preload("res://source_clock.gd")
const Session := preload("res://rollback_test_session.gd")


class Counter extends RefCounted:
	var calls := 0
	var label := ""
	var trace: Array = []
	func enter_frame() -> void:
		calls += 1
		trace.append(label)


# A deliberately small fixture using the real RNG/clock services. It is not a
# FighterRuntime substitute and passing it cannot certify a battle snapshot.
class Fixture extends RefCounted:
	var random := SourceRandom.new()
	var clock := Clock.new()
	var frame := 0
	var total := 0.0
	var children: Array = []
	var previous := {"p1": false, "p2": false}
	func _init() -> void:
		random.use_seed(12093)
		clock.use_explicit_time(0)
	func advance(next: int, players: Dictionary) -> String:
		if next != frame + 1:
			return "Non-contiguous fixture frame"
		frame = next
		clock.set_explicit_time(frame * 100)
		for slot in ["p1", "p2"]:
			if players[slot].attack and not previous[slot]:
				children.append({"born": frame, "value": random.next_value(slot), "undefined": null})
			previous[slot] = players[slot].attack
		for index in range(children.size() - 1, -1, -1):
			total += children[index].value
			if frame - children[index].born >= 4:
				children.remove_at(index)
		total += float(clock.read("fixture")) / 1000.0
		return ""
	func save_state() -> Dictionary:
		return State.pack_state("service-fixture-v1", frame, {"random": random.save_state(),
			"clock": clock.save_state(), "fixture": {"total": total,
			"children": children.duplicate(true), "previous": previous.duplicate()}})
	func validate_state(snapshot: Dictionary) -> String:
		var problem := State.validate_snapshot(snapshot, "service-fixture-v1", ["random", "clock", "fixture"])
		if not problem.is_empty(): return problem
		problem = random.validate_state(snapshot.owners.random)
		if not problem.is_empty(): return problem
		return clock.validate_state(snapshot.owners.clock)
	func load_state(snapshot: Dictionary) -> String:
		var problem := validate_state(snapshot)
		if not problem.is_empty(): return problem
		random.load_state(snapshot.owners.random)
		clock.load_state(snapshot.owners.clock)
		frame = snapshot.frame
		total = snapshot.owners.fixture.total
		children = snapshot.owners.fixture.children.duplicate(true)
		previous = snapshot.owners.fixture.previous.duplicate()
		return ""


func _initialize() -> void:
	_run.call_deferred()


func _buttons(attack: bool) -> Dictionary:
	var held := {}
	for button in Session.BUTTONS:
		held[button] = button == "attack" and attack
	return held


func _players(frame: int) -> Dictionary:
	return {"p1": _buttons(frame % 11 < 4), "p2": _buttons(frame % 7 < 3)}


func _run() -> void:
	_test_values()
	_test_services()
	_test_registry()
	_test_restore()
	_test_delayed_inputs()
	_test_input_delay()
	print("ROLLBACK_SERVICES_SMOKE_OK scope=services_and_synthetic_fixture_not_battle")
	quit()


func _test_values() -> void:
	var original := {"b": [null, false, 9223372036854775807], "a": 1.25}
	var snapshot := State.pack_state("build", 0, original)
	original.b[0] = true
	assert(snapshot.owners.b[0] == null)
	assert(State.fingerprint(snapshot) == State.fingerprint(bytes_to_var(var_to_bytes(snapshot))))
	assert(State.fingerprint({"b": false, "a": null}) == State.fingerprint({"a": null, "b": false}))
	assert(State.fingerprint({"a": null}) != State.fingerprint({"a": false}))
	assert(not State.validate_value({"node": self}).is_empty())
	assert(not State.validate_value({"callback": _run}).is_empty())
	assert(State.first_difference({"a": [0, null]}, {"a": [0, false]}) == "$.a[1]: type differs")
	var bad := snapshot.duplicate(true)
	bad.version += 1
	assert(not State.validate_snapshot(bad, "build", ["a", "b"]).is_empty())
	assert(not State.validate_snapshot(snapshot, "another-build", ["a", "b"]).is_empty())
	assert(not State.validate_snapshot(snapshot, "build", ["a", "b", "missing"]).is_empty())


func _test_services() -> void:
	var random := SourceRandom.new()
	random.use_seed(4096)
	var state := random.save_state()
	var values := []
	for index in 32: values.append(random.next_value("hit"))
	assert(random.load_state(state).is_empty())
	for index in 32: assert(random.next_value("hit") == values[index])
	var before := random.save_state()
	var invalid := before.duplicate(true)
	invalid.cursor = -1
	assert(not random.load_state(invalid).is_empty())
	assert(random.save_state() == before)
	assert(random.use_recorded_tape([{"index": 1, "site": "hit", "value": 0.25}]))
	state = random.save_state()
	assert(random.next_value("hit") == 0.25 and random.replay_complete())
	assert(random.load_state(state).is_empty())
	assert(random.next_value("hit") == 0.25)
	var clock := Clock.new()
	assert(not clock.load_state(clock.save_state()).is_empty())
	assert(clock.use_explicit_time(300))
	assert(clock.read("voice") == 300)
	state = clock.save_state()
	assert(clock.set_explicit_time(450))
	assert(clock.read("voice") == 450)
	assert(not clock.set_explicit_time(449))
	assert(clock.load_state(state).is_empty())
	assert(clock.read("voice") == 300)
	assert(clock.use_recorded_tape([{"index": 1, "site": "voice", "value": 801}]))
	state = clock.save_state()
	assert(clock.read("voice") == 801 and clock.replay_complete())
	assert(clock.load_state(state).is_empty())
	assert(clock.read("voice") == 801)


func _test_registry() -> void:
	var registry := SourceCallbackRegistry.new()
	var older := Counter.new()
	var newer := Counter.new()
	older.label = "old"
	newer.label = "new"
	var trace := []
	older.trace = trace
	newer.trace = trace
	var targets := {"old": older, "new": newer}
	var identify := func(target: Object) -> String: return target.label
	var resolve := func(id: String) -> Object: return targets.get(id)
	var first := registry.register(older, "enter_frame", 0)
	registry.register(newer, "enter_frame", 1)
	var snapshot := registry.save_state(identify)
	assert(State.validate_value(snapshot).is_empty())
	registry.dispatch(1)
	assert(trace == ["old"])
	registry.unregister(first)
	assert(registry.load_state(snapshot, resolve).is_empty())
	trace.clear()
	registry.dispatch(2)
	assert(trace == ["new", "old"])
	var before := registry.save_state(identify)
	var invalid := before.duplicate(true)
	invalid.entries[0].target = "missing"
	assert(not registry.load_state(invalid, resolve).is_empty())
	assert(registry.save_state(identify) == before)
	assert(registry.register(older, "enter_frame", 2) == 3)


func _test_restore() -> void:
	var fixture := Fixture.new()
	var states := [fixture.save_state()]
	for frame in range(1, 81):
		assert(fixture.advance(frame, _players(frame)).is_empty())
		states.append(fixture.save_state())
	# Before/during/after dynamic children; each restore reruns multiple frames.
	for start in range(0, 70):
		assert(fixture.load_state(states[start]).is_empty())
		assert(fixture.save_state() == states[start])
		for frame in range(start + 1, start + 11):
			assert(fixture.advance(frame, _players(frame)).is_empty())
			assert(State.first_difference(fixture.save_state(), states[frame]).is_empty())
	# An alternative continuation must not mutate the stored branch.
	assert(fixture.load_state(states[12]).is_empty())
	fixture.advance(13, {"p1": _buttons(false), "p2": _buttons(false)})
	assert(fixture.load_state(states[12]).is_empty())
	fixture.advance(13, _players(13))
	assert(fixture.save_state() == states[13])


func _test_delayed_inputs() -> void:
	var fixture := Fixture.new()
	var session := Session.new()
	assert(session.configure(fixture, "epoch-1", 6, 16).is_empty())
	assert(not session.receive("old-epoch", "p1", 1, _buttons(false)).is_empty())
	assert(not session.receive("epoch-1", "p1", 1, {}).is_empty())
	var reference := Fixture.new()
	var states := [reference.save_state()]
	for frame in range(1, 121):
		reference.advance(frame, _players(frame))
		states.append(reference.save_state())
	for frame in range(1, 121):
		assert(session.receive("epoch-1", "p1", frame, _players(frame).p1).is_empty())
		assert(session.step().is_empty())
		# Bursts deliberately deliver newest first; duplicates are idempotent.
		if frame % 5 == 0:
			for delayed in range(frame, frame - 5, -1):
				assert(session.receive("epoch-1", "p2", delayed, _players(delayed).p2).is_empty())
				assert(session.receive("epoch-1", "p2", delayed, _players(delayed).p2).is_empty())
			assert(session.confirmed == frame)
			assert(State.first_difference(session.state_at(frame), states[frame]).is_empty())
			for confirmed_frame in range(session.oldest_frame(), frame + 1):
				assert(session.state_at(confirmed_frame) == states[confirmed_frame])
	assert(session.rollback_count > 0 and session.replayed_frames > session.rollback_count)
	assert(session.oldest_frame() > 0 and session._states.size() <= 16)
	assert(not session.receive("epoch-1", "p2", 1, _buttons(false)).is_empty())
	assert(not session.receive("epoch-1", "p2", 120, _buttons(not _players(120).p2.attack)).is_empty())
	var frozen := session.state_at(120)
	for index in 6: assert(session.step().is_empty())
	assert(session.step() == "waiting_for_input")
	assert(session.frontier == 126 and session.state_at(120) == frozen)
	var zero := Session.new()
	assert(zero.configure(Fixture.new(), "zero", 0, 2).is_empty())
	assert(zero.step() == "waiting_for_input")
	assert(zero.receive("zero", "p1", 1, _buttons(false)).is_empty())
	assert(zero.receive("zero", "p2", 1, _buttons(false)).is_empty())
	assert(zero.step().is_empty())
	print("ROLLBACK_FAULTS corrections=", session.rollback_count, " replayed=", session.replayed_frames,
		" retained_bytes=", session.retained_bytes())


func _test_input_delay() -> void:
	var fixture := Fixture.new()
	var session := Session.new()
	assert(session.configure(fixture, "delay", 0, 4, 2).is_empty())
	var packet := session.sample_local("p1", 1, _buttons(true))
	assert(packet.frame == 3)
	assert(session.sample_local("p1", 1, _buttons(false)).has("error"))
	assert(session.step().is_empty() and fixture.previous.p1 == false)
	assert(session.step().is_empty() and fixture.previous.p1 == false)
	assert(session.step() == "waiting_for_input")
	assert(session.receive("delay", "p2", 3, _buttons(false)).is_empty())
	assert(session.step().is_empty() and fixture.previous.p1 == true)
