extends SceneTree


class TraceTarget extends RefCounted:
	var calls := 0

	func on_clip() -> void:
		calls += 1


class Harness extends RefCounted:
	var held_target: Object

	func drop_delegate() -> void:
		held_target = null


var observed_events: Array = []
var traced_instance_id := -1


func _initialize() -> void:
	_run.call_deferred()


func _identity_for(instance_id: int) -> Dictionary:
	if instance_id == traced_instance_id:
		return {"source_path": "test/clip", "slot": "p2"}
	return {}


func _observe(event: Dictionary) -> void:
	observed_events.append(event)


func _run() -> void:
	var observed = load("res://tests/callback_trace_registry.gd").new()
	observed.identity_lookup = Callable(self, "_identity_for")
	observed.observer = Callable(self, "_observe")
	observed.traced_paths["test/clip"] = true

	var harness := Harness.new()
	harness.held_target = TraceTarget.new()
	traced_instance_id = harness.held_target.get_instance_id()
	observed.register(harness.held_target, "frame_1133_depth_30", 0)
	observed.register(harness, "drop_delegate", 0)
	observed.dispatch(1)
	assert(observed_events.is_empty(), "dead delegate emitted a ghost enter/exit pair")
	assert(observed.size() == 1, "dead proxy registration was not removed during the same dispatch")
	assert(observed._proxies.is_empty(), "dead proxy remained retained after removal")

	var live := TraceTarget.new()
	traced_instance_id = live.get_instance_id()
	observed.register(live, "frame_1133_depth_30", 1)
	assert(observed.size() == 2 and observed._proxies.size() == 1)
	observed.clear()
	assert(observed.size() == 0 and observed._proxies.is_empty(), "clear left proxy references behind")

	print("CALLBACK_TRACE_REGISTRY_SMOKE_OK")
	quit()
