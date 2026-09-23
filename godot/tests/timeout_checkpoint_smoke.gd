extends SceneTree


class Target extends RefCounted:
	var scheduler: AiSourceTimeouts
	var observed: Array = []
	func first() -> void:
		observed.append("first")
		scheduler.schedule(second, 600)
	func second() -> void:
		observed.append("second")


func _initialize() -> void:
	var scheduler := AiSourceTimeouts.new()
	scheduler.recorded = true
	root.add_child(scheduler)
	var target := Target.new()
	target.scheduler = scheduler
	var identify := func(_target: Object) -> String: return "body"
	var resolve := func(_id: String) -> Object: return target
	var id := scheduler.schedule(target.first, 800)
	var snapshot := scheduler.save_state(identify)
	assert(not snapshot.has("error"))
	assert(scheduler.fire_recorded(id))
	assert(target.observed == ["first"])
	assert(scheduler.fire_recorded(id + 1))
	assert(target.observed == ["first", "second"])
	# A reconstructed BODY receives the restored callback; no captured old target
	# or synthetic registration signal should be needed to recreate the queue.
	var replacement := Target.new()
	replacement.scheduler = scheduler
	var registrations := []
	scheduler.registered.connect(func(new_id: int, _delay: int) -> void: registrations.append(new_id))
	assert(scheduler.load_state(snapshot, func(_key: String) -> Object: return replacement).is_empty())
	assert(registrations.is_empty())
	assert(scheduler.save_state(identify) == snapshot)
	assert(scheduler.fire_recorded(id))
	assert(replacement.observed == ["first"] and target.observed == ["first", "second"])
	assert(registrations == [id + 1])
	var before := scheduler.save_state(identify)
	var invalid := before.duplicate(true)
	invalid.delays[str(id + 1)] = -1
	assert(not scheduler.load_state(invalid, resolve).is_empty())
	assert(scheduler.save_state(identify) == before)
	assert(scheduler.fire_recorded(id + 1))
	assert(replacement.observed == ["first", "second"])
	assert(not scheduler.fire_recorded(id + 1))
	scheduler.recorded = false
	assert(scheduler.save_state(identify).has("error"))
	assert(not scheduler.load_state(snapshot, resolve).is_empty())
	scheduler.free()
	print("TIMEOUT_CHECKPOINT_SMOKE_OK targets=rebound nested_ids=restored invalid=atomic live=rejected")
	quit()
