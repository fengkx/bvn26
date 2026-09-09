class_name AiControllerInstances
extends RefCounted

# The host supplies display-list order; this class must not guess callback order.
var _instances: Dictionary = {}
var _next_generation: int = 0
var registry: SourceCallbackRegistry


func synchronize(hooks: Array, source_frame: int, display_tick: int, factory: Callable) -> void:
	var retained := {}
	for hook: Dictionary in hooks:
		if source_frame not in hook["member_frames"]:
			continue
		var key := str(hook["path"])
		retained[key] = true
		if _instances.has(key):
			continue
		_next_generation += 1
		_instances[key] = {
			"generation": _next_generation,
			"placed_tick": display_tick,
			"controller": factory.call(hook, _next_generation),
			"method": hook["method"],
		}
		if registry != null:
			_instances[key]["registration"] = registry.register(
				_instances[key]["controller"], hook["method"], display_tick)
	for key: String in _instances.keys():
		if not retained.has(key):
			if registry != null:
				registry.unregister(_instances[key]["registration"])
			_instances.erase(key)


func alive(path: String, generation: int) -> bool:
	return _instances.has(path) and _instances[path]["generation"] == generation


func advance_children(display_tick: int) -> void:
	for instance: Dictionary in _instances.values():
		if int(instance["placed_tick"]) < display_tick and instance["controller"].has_method("advance_timeline"):
			instance["controller"].advance_timeline(display_tick)


func dispatch(ordered_paths: Array, display_tick: int) -> void:
	# Capture identity before callbacks. A goto may remove and re-place the same
	# authored hook; the replacement must not inherit this tick's callback.
	var callbacks: Array = []
	for path: String in ordered_paths:
		if not _instances.has(path):
			continue
		var instance: Dictionary = _instances[path]
		if int(instance["placed_tick"]) >= display_tick:
			continue
		callbacks.append([path, instance.duplicate()])
	for callback: Array in callbacks:
		var instance: Dictionary = callback[1]
		if alive(callback[0], instance["generation"]):
			instance["controller"].call(instance["method"])


func clear() -> void:
	if registry != null:
		for instance: Dictionary in _instances.values():
			registry.unregister(instance["registration"])
	_instances.clear()
