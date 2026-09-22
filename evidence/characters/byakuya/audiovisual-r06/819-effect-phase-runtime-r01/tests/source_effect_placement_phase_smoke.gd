extends SceneTree


var registry := SourceCallbackRegistry.new()
var holder := Node.new()
var spawned_during_dispatch: HitEffectRuntime


func _initialize() -> void:
	_run.call_deferred()


func _make_effect() -> HitEffectRuntime:
	var effect := HitEffectRuntime.new()
	effect.auto_advance = false
	effect.defer_initial_frame = true
	holder.add_child(effect)
	effect.configure("XG_fzcc", Vector2.ZERO, 1)
	return effect


func _spawn_during_dispatch() -> void:
	spawned_during_dispatch = _make_effect()
	spawned_during_dispatch.register_source_frames(registry, registry.current_tick)
	# A child registered during dispatch must not receive the current callback.
	# Its first source callback belongs to the following display tick; advancing
	# it inline here would encode the rejected synthetic +1 expectation.


func _run() -> void:
	root.add_child(holder)
	var placed_before_dispatch := _make_effect()
	placed_before_dispatch.register_source_frames(registry, 0)
	registry.dispatch(0)
	assert(placed_before_dispatch.effect_frame == 1)
	registry.dispatch(1)
	assert(placed_before_dispatch.effect_frame == 2)

	# Use a bound callable so the creation happens inside registry.dispatch.
	var spawn_id := registry.register(self, &"_spawn_during_dispatch", 1)
	registry.dispatch(2)
	assert(spawned_during_dispatch != null and spawned_during_dispatch.effect_frame == 1)
	registry.unregister(spawn_id)
	registry.dispatch(3)
	assert(spawned_during_dispatch.effect_frame == 2)

	spawned_during_dispatch.queue_free()
	await process_frame
	var rebuilt := _make_effect()
	rebuilt.register_source_frames(registry, registry.current_tick)
	assert(rebuilt.effect_frame == 1)
	rebuilt.advance_effect()
	assert(rebuilt.effect_frame == 2)

	print("SOURCE_EFFECT_PLACEMENT_PHASE_SMOKE_OK")
	quit()
