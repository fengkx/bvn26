extends SceneTree

const Authority = preload("res://online_timer_authority.gd")
const State = preload("res://simulation_state.gd")

class Driver extends Node:
	var timeouts := AiSourceTimeouts.new()

class Player extends Node:
	var _driver: Driver

class Intro extends RefCounted:
	var active := false
	var polling := false
	var spec := {"poll_ms": 500}

class Scene extends Node:
	var countdown: Node
	var battle_intro := Intro.new()
	var ko_interval_sequence := 0
	var ko_nextfight_timer: Timer
	var player_body_driver: Player
	var opponent_driver: Driver
	var source_root_intervals: SourceRootIntervals

class Receiver extends RefCounted:
	var calls: Array = []
	func record(label: String) -> void:
		calls.append(label)

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var game := Scene.new()
	root.add_child(game)
	game.player_body_driver = Player.new()
	game.add_child(game.player_body_driver)
	game.player_body_driver._driver = Driver.new()
	game.player_body_driver.add_child(game.player_body_driver._driver)
	game.opponent_driver = Driver.new()
	game.add_child(game.opponent_driver)
	for driver in [game.player_body_driver._driver, game.opponent_driver]:
		driver.timeouts.recorded = true
		driver.add_child(driver.timeouts)
	var owner := SourceRootIntervals.new()
	owner.recorded = true
	game.source_root_intervals = owner
	game.add_child(owner)
	var target := Receiver.new()
	var authority := Authority.new()
	assert(authority.configure(game, 0).is_empty())
	var old_id := owner.assign_interval("feiint", target.record.bind("old"), 1000)
	var new_id := owner.assign_interval("feiint", target.record.bind("new"), 700)
	var other_id := owner.assign_interval("feiint2", target.record.bind("p2"), 1000)
	assert(old_id != new_id and new_id != other_id)
	authority.finish_frame()
	assert(_deliver(authority, owner, 699, 1).is_empty())
	var early := _deliver(authority, owner, 701, 2)
	assert(early.size() == 1 and early[0].id == new_id and early[0].due_ms == 700)
	var equal_deadline := _deliver(authority, owner, 1003, 3)
	assert(equal_deadline.size() == 2 and equal_deadline[0].id == old_id and equal_deadline[1].id == other_id)
	assert(target.calls == ["new", "old", "p2"])
	assert(_deliver(authority, owner, 1003, 3).is_empty(), "One sample repeated an interval delivery")
	var timer_snapshot: Dictionary = authority.save_state(3)
	var queue_snapshot := owner.save_state(func(value): return "receiver" if value == target else "")
	assert(not queue_snapshot.has("error"), str(queue_snapshot))
	var before_calls := target.calls.duplicate()
	var expected_events := _tail(authority, owner, old_id, new_id, other_id)
	var expected_calls := target.calls.duplicate()
	var expected_state: Dictionary = authority.save_state(5)
	assert(owner.load_state(queue_snapshot, func(id): return target if id == "receiver" else null).is_empty())
	assert(authority.load_state(timer_snapshot).is_empty())
	target.calls = before_calls.duplicate()
	var actual_events := _tail(authority, owner, old_id, new_id, other_id)
	assert(State.canonical(expected_events) == State.canonical(actual_events))
	assert(target.calls == expected_calls)
	assert(State.first_difference(expected_state, authority.save_state(5)).is_empty())
	for invalid in [null, {"0": 100}, {"01": 100}, {"1": -1}, {"1": 1.5}]:
		var broken := expected_state.duplicate(true)
		broken.root_due_ms = invalid
		assert(not authority.load_state(broken).is_empty())
		assert(State.first_difference(expected_state, authority.save_state(5)).is_empty())
	var next_match := SourceRootIntervals.new()
	next_match.recorded = true
	game.add_child(next_match)
	game.source_root_intervals = next_match
	var next_id := next_match.assign_interval("feiint", target.record.bind("next_match"), 77)
	assert(next_id == old_id, "Fixture must reuse an ID in a different queue")
	authority.finish_frame()
	assert(authority.root_due_ms == {str(next_id): 4077})
	assert(_deliver(authority, next_match, 4076, 6).is_empty())
	assert(_deliver(authority, next_match, 4077, 7).size() == 1)
	assert(target.calls[-1] == "next_match")
	owner.clear()
	next_match.clear()
	authority.finish_frame()
	assert(authority.root_due_ms.is_empty())
	game.free()
	print("ONLINE_ROOT_INTERVAL_AUTHORITY_SMOKE_OK independent_ids=3 repeating=true irregular_samples=true bounded_resume=true replay_callbacks=true replay_deadlines=true malformed_rejected=5 new_match_id_reuse=true")
	quit()

func _tail(authority: RefCounted, owner: SourceRootIntervals, old_id: int, new_id: int, other_id: int) -> Array:
	var events := _deliver(authority, owner, 1405, 4)
	assert(events.size() == 1 and events[0].id == new_id and events[0].due_ms == 1401)
	assert(owner.clear_interval("feiint"))
	assert(owner._pending.has(old_id) and not owner._pending.has(new_id))
	var resumed := _deliver(authority, owner, 4000, 5)
	assert(resumed.size() == 2 and resumed[0].id == old_id and resumed[1].id == other_id)
	assert(resumed[0].due_ms == 2003 and resumed[1].due_ms == 2003)
	assert(authority.root_due_ms == {str(old_id): 5000, str(other_id): 5000})
	events.append_array(resumed)
	return events

func _deliver(authority: RefCounted, owner: SourceRootIntervals, sample: int, frame: int) -> Array:
	assert(authority.set_time(sample).is_empty())
	var events: Array = authority.events_for_phase("after_actor_advance", frame)
	assert(authority.error.is_empty(), authority.error)
	for event in events:
		assert(event.kind == "root_interval" and event.phase == "after_actor_advance")
		assert(owner.fire_recorded(event.id))
	authority.finish_frame()
	return events
