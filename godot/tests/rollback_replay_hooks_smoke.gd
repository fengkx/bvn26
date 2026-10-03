extends SceneTree

const State := preload("res://simulation_state.gd")
const Session := preload("res://rollback_test_session.gd")
const HelperScript := preload("res://helper_runtime.gd")
const Presentation := preload("res://rollback_presentation.gd")


class DiagnosticRecorder extends Node:
	var events: Array[Dictionary] = []

	func push_event(event_type: String, payload: Dictionary, tick: int) -> void:
		events.append({"type": event_type, "payload": payload.duplicate(true), "tick": tick})


class Adapter extends RefCounted:
	const PresentationHelper := preload("res://rollback_presentation.gd")
	var frame := 0
	var score := 0
	var replaying := false
	var begin_count := 0
	var end_count := 0
	var fail_mode := ""
	var helper: Node
	var console_allowed: Array[bool] = []
	var replay_start_console_allowed := true

	func advance(next_frame: int, players: Dictionary) -> String:
		if next_frame != frame + 1:
			return "Non-contiguous replay fixture frame"
		console_allowed.append(PresentationHelper.should_emit_combat_console_event(helper))
		helper.set("diagnostic_tick", next_frame)
		helper.call("_emit_diagnostic", "fixture_advance", {"frame": next_frame})
		if replaying and fail_mode == "advance":
			return "injected replay advance failure"
		var attack_score := 0
		for slot in ["p1", "p2"]:
			if players[slot].attack:
				attack_score += next_frame
		frame = next_frame
		score += attack_score
		return ""

	func save_state() -> Dictionary:
		if replaying and fail_mode == "save":
			return {"error": "injected replay save failure"}
		return State.pack_state("replay-hook-fixture-v1", frame, {"score": score})

	func validate_state(snapshot: Dictionary) -> String:
		if replaying and fail_mode == "validate":
			return "injected replay validation failure"
		var problem := State.validate_snapshot(snapshot, "replay-hook-fixture-v1", ["score"])
		if not problem.is_empty():
			return problem
		return ""

	func load_state(snapshot: Dictionary) -> String:
		if replaying and fail_mode == "load":
			return "injected replay load failure"
		frame = snapshot.frame
		score = snapshot.owners.score
		return ""

	func begin_replay() -> void:
		begin_count += 1
		replaying = true
		replay_start_console_allowed = PresentationHelper.should_emit_combat_console_event(helper)

	func end_replay() -> void:
		end_count += 1
		replaying = false


func _initialize() -> void:
	_run.call_deferred()


func _buttons(attack: bool) -> Dictionary:
	var held := {}
	for button in Session.BUTTONS:
		held[button] = button == "attack" and attack
	return held


func _frame_players(frame: int) -> Dictionary:
	return {"p1": _buttons(frame == 3), "p2": _buttons(frame == 2)}


func _make_adapter(recorder: DiagnosticRecorder) -> Adapter:
	var adapter := Adapter.new()
	var helper := HelperScript.new()
	helper.set("diagnostic_runtime", recorder)
	helper.set_meta("rollback_owner", adapter)
	adapter.helper = helper
	return adapter


func _advance_predicted(session: RefCounted) -> void:
	for frame in range(1, 4):
		assert(session.receive("replay-test", "p1", frame, _frame_players(frame).p1).is_empty())
		if frame == 3:
			assert(session.receive("replay-test", "p2", frame, _frame_players(frame).p2).is_empty())
		assert(session.step().is_empty())


func _run() -> void:
	_test_successful_correction()
	for deferred in [false, true]:
		for failure in ["validate", "load", "advance", "save"]:
			_test_failure_cleanup(failure, deferred)
	print("ROLLBACK_REPLAY_HOOKS_SMOKE_OK correction_state_equal=true replay_diagnostics_tagged=true predicted_events_retained=true failure_cleanup=8")
	quit()


func _test_successful_correction() -> void:
	var recorder := DiagnosticRecorder.new()
	var adapter := _make_adapter(recorder)
	var session := Session.new()
	assert(session.configure(adapter, "replay-test", 6, 16).is_empty())
	assert(Presentation.should_emit_combat_console_event(adapter.helper))
	_advance_predicted(session)
	var original_events := recorder.events.size()
	assert(original_events == 3)
	assert(session.receive("replay-test", "p2", 2, _buttons(true)).is_empty())
	assert(not adapter.replaying)
	assert(adapter.begin_count == 1 and adapter.end_count == 1)
	assert(adapter.console_allowed == [true, true, true, false, false])
	assert(not adapter.replay_start_console_allowed)
	assert(recorder.events.size() == original_events + 2)
	var original_predicted_frame_two := false
	var replay_frame_two := false
	for event in recorder.events:
		if int(event.payload.get("frame", -1)) != 2:
			continue
		if bool(event.payload.get("replay", false)):
			replay_frame_two = true
		else:
			original_predicted_frame_two = true
	assert(original_predicted_frame_two and replay_frame_two)

	var reference_recorder := DiagnosticRecorder.new()
	var reference := _make_adapter(reference_recorder)
	var reference_session := Session.new()
	assert(reference_session.configure(reference, "reference", 6, 16).is_empty())
	for frame in range(1, 4):
		for slot in ["p1", "p2"]:
			assert(reference_session.receive("reference", slot, frame, _frame_players(frame)[slot]).is_empty())
		assert(reference_session.step().is_empty())
	assert(State.first_difference(adapter.save_state(), reference.save_state()).is_empty())
	adapter.helper.free()
	reference.helper.free()
	recorder.free()
	reference_recorder.free()


func _test_failure_cleanup(failure: String, deferred: bool) -> void:
	var recorder := DiagnosticRecorder.new()
	var adapter := _make_adapter(recorder)
	var session := Session.new()
	assert(session.configure(adapter, "replay-test", 6, 16).is_empty())
	_advance_predicted(session)
	adapter.fail_mode = failure
	var problem: String = session.receive("replay-test", "p2", 2, _buttons(true), deferred)
	if deferred:
		assert(problem.is_empty() and adapter.begin_count == 0)
		problem = session.reconcile()
	assert(not problem.is_empty(), "Expected injected %s failure" % failure)
	var pending: Dictionary = session.pending_correction()
	assert(pending.target == 3 and pending.actual.p2.has(2) and pending.actual.p2.has(3))
	assert(not adapter.replaying, "Replay flag remained set after %s failure" % failure)
	assert(adapter.begin_count == 1 and adapter.end_count == 1,
		"Replay hooks were not balanced after %s failure" % failure)
	assert(not adapter.replay_start_console_allowed,
		"Replay console gate was open at replay start for %s failure" % failure)
	if failure in ["advance", "save"]:
		assert(not adapter.console_allowed.is_empty() and not adapter.console_allowed[-1],
			"Replay console gate was open during %s failure" % failure)
	adapter.helper.free()
	recorder.free()
