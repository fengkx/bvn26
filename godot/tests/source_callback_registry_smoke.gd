extends SceneTree


class Callback extends RefCounted:
	var label: String
	var events: Array
	var effect: Callable

	func run() -> void:
		events.append(label)
		if effect.is_valid():
			effect.call()


func _initialize() -> void:
	var registry := SourceCallbackRegistry.new()
	var events: Array = []
	var targets: Array[Callback] = []
	var ids: Array[int] = []
	for label: String in ["a.body", "a.child", "b.body", "b.child"]:
		var target := Callback.new()
		target.label = label
		target.events = events
		targets.append(target)
		ids.append(registry.register(target, "run", 0))
	registry.dispatch(0)
	assert(events.is_empty())
	registry.dispatch(1)
	assert(events == ["b.child", "b.body", "a.child", "a.body"])
	# Retained instances and depth swaps do not register a new callback.
	events.clear()
	registry.dispatch(2)
	assert(events == ["b.child", "b.body", "a.child", "a.body"])
	registry.unregister(ids[1])
	ids[1] = registry.register(targets[1], "run", 6)
	events.clear()
	registry.dispatch(6)
	assert(events == ["b.child", "b.body", "a.body"])
	events.clear()
	registry.dispatch(7)
	assert(events == ["a.child", "b.child", "b.body", "a.body"])
	registry.unregister(ids[3])
	ids[3] = registry.register(targets[3], "run", 14)
	events.clear()
	registry.dispatch(15)
	assert(events == ["b.child", "a.child", "b.body", "a.body"])
	# A callback may invalidate a pending entry and recreate the same source hook.
	targets[3].effect = func() -> void:
		registry.unregister(ids[1])
		ids[1] = registry.register(targets[1], "run", 16)
	events.clear()
	registry.dispatch(16)
	assert(events == ["b.child", "b.body", "a.body"])
	targets[3].effect = Callable()
	registry.clear()
	assert(registry.size() == 0)
	print("SOURCE_CALLBACK_REGISTRY_SMOKE_OK")
	quit()
