extends SceneTree


class Observer extends RefCounted:
	var label: String
	var effect: HitEffectRuntime
	var events: Array

	func run() -> void:
		events.append([label, effect.effect_frame, effect.game_paused])


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var registry := SourceCallbackRegistry.new()
	var events: Array = []
	var effect := HitEffectRuntime.new()
	var older := Observer.new()
	older.label = "old"
	older.effect = effect
	older.events = events
	registry.register(older, "run", 0)
	root.add_child(effect)
	effect.configure("XG_qdjx", Vector2.ZERO, 1)
	effect.register_source_frames(registry, 0)
	registry.dispatch(0)
	assert(events.is_empty() and effect.effect_frame == 1)
	registry.dispatch(1)
	assert(events == [["old", 2, true]])
	var later := Observer.new()
	later.label = "late"
	later.effect = effect
	later.events = events
	registry.register(later, "run", 1)
	for tick in range(2, 15):
		events.clear()
		registry.dispatch(tick)
	assert(events == [["late", 14, true], ["old", 15, false]])
	effect.queue_free()
	await process_frame
	assert(registry.size() == 2)
	registry.clear()
	print("EFFECT_CALLBACK_ORDER_SMOKE_OK")
	quit()
