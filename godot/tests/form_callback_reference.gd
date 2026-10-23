extends SceneTree

var fighter: FighterRuntime
var observed: Array


class LoseHpOverride extends RefCounted:
	var fighter: FighterRuntime
	func loseHp(amount: Variant) -> void:
		fighter.health -= float(amount) * 2


func _initialize() -> void:
	_run.call_deferred()


func deliver(callback: Callable, label: String, health: float, paused_source: bool, invulnerable: bool) -> void:
	fighter.health = health
	fighter.root_zhanting = paused_source
	fighter.ai_source_state.values["wudi"] = invulnerable
	callback.call()
	observed.append({"key": label, "value": str(int(fighter.health))})


func _run() -> void:
	var directory := "res://tests/fixtures/form_callbacks"
	var fixtures: Array = JSON.parse_string(FileAccess.get_file_as_string(directory.path_join("sources.json")))
	var native: Array = JSON.parse_string(FileAccess.get_file_as_string("res://../evidence/importer-loud-fail/r10/callback-observations.json"))
	var compared := 0
	for index in fixtures.size():
		var fixture: Dictionary = fixtures[index]
		assert(native[index].fighter.to_lower() == str(fixture.fighter).to_lower())
		# Use the actual BODY adapter but isolate callback semantics from assets and
		# the still-unimplemented full profile replacement transaction.
		fighter = FighterRuntime.new()
		fighter.max_health = 1000
		var context := AiBodyContext.new(fighter)
		context._scalar_fields = PackedStringArray(fixture.metadata.scalar_fields)
		var body: RefCounted = load(directory.path_join(fixture.script)).new({})
		body.adapter = context
		fighter.source_body = body
		var callback := Callable(body, "feixue")
		observed = []
		deliver(callback, "before", 500, false, false)
		deliver(callback, "paused", 500, true, false)
		deliver(callback, "threshold", 200, false, false)
		deliver(callback, "above_threshold", 201, false, false)
		deliver(callback, "invulnerable", 500, false, true)
		var scheduler := AiSourceTimeouts.new()
		scheduler.recorded = true
		root.add_child(scheduler)
		var id := scheduler.schedule(callback, 1000, true)
		var function_ref: WeakRef = weakref(body)
		# Deliberately replace the body state object, not just a field. Retained
		# compiled code resolves state through the stable wrapper on each call.
		fighter.ai_source_state = AiSourceState.new()
		var new_context := AiBodyContext.new(fighter)
		new_context._scalar_fields = PackedStringArray(fixture.metadata.scalar_fields)
		var replacement: RefCounted = load(directory.path_join(fixture.script)).new({})
		replacement.adapter = new_context
		fighter.source_body = replacement
		deliver(callback, "after", 600, false, false)
		deliver(callback, "after_paused", 600, true, false)
		deliver(callback, "after_threshold", 200, false, false)
		deliver(callback, "after_invulnerable", 600, false, true)
		var override := LoseHpOverride.new()
		override.fighter = fighter
		fighter.source_body = override
		deliver(callback, "rebound_method", 600, false, false)
		fighter.source_body = replacement
		fighter.health = 600
		fighter.root_zhanting = false
		fighter.ai_source_state.values["wudi"] = false
		callback = Callable()
		body = null
		context = null
		assert(function_ref.get_ref() != null, "Interval lost its captured function")
		for delivery in 2:
			assert(scheduler.fire_recorded(id))
			observed.append({"key": "interval", "value": str(int(fighter.health))})
		assert(scheduler.cancel(id))
		assert(not scheduler.fire_recorded(id))
		assert(function_ref.get_ref() == null, "Cancelled interval retained the old function")
		var expected: Array = native[index].events.filter(func(event: Dictionary) -> bool: return event.key not in ["replaced", "done"])
		assert(observed == expected, "Compiled callback differs from native: " + fixture.fighter)
		compared += observed.size()
		scheduler.free()
		fighter.source_body = null
		fighter.free()
	print("FORM_CALLBACK_REFERENCE_OK 4/4 cases ", compared, "/", compared, " callback observations; full replacement not asserted")
	quit()
