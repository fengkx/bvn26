extends SceneTree

class Controller extends RefCounted:
	var ticks: int = 0
	var callback: Callable

	func enter_frame() -> void:
		ticks += 1
		if callback.is_valid():
			callback.call()


func _initialize() -> void:
	var instances := AiControllerInstances.new()
	var created: Array = []
	var factory := func(_hook: Dictionary, generation: int) -> RefCounted:
		var controller := Controller.new()
		created.append([controller, generation])
		return controller
	# Membership models a retained instance across a goto, followed by removal.
	var hooks: Array = [{"path": "a", "method": "enter_frame", "member_frames": [1, 2]}]
	instances.synchronize(hooks, 1, 0, factory)
	instances.dispatch(["a"], 0)
	assert(created[0][0].ticks == 0)
	instances.dispatch(["a"], 1)
	assert(created[0][0].ticks == 1)
	instances.synchronize(hooks, 2, 1, factory)
	assert(created.size() == 1)
	assert(instances.alive("a", created[0][1]))
	instances.synchronize(hooks, 3, 1, factory)
	assert(not instances.alive("a", created[0][1]))
	instances.synchronize(hooks, 1, 1, factory)
	assert(created.size() == 2)
	instances.dispatch(["a"], 1)
	assert(created[1][0].ticks == 0)
	instances.dispatch(["a"], 2)
	assert(created[1][0].ticks == 1)
	instances.clear()
	assert(not instances.alive("a", created[1][1]))
	var pair: Array = [
		{"path": "a", "method": "enter_frame", "member_frames": [1]},
		{"path": "b", "method": "enter_frame", "member_frames": [1]},
	]
	instances.synchronize(pair, 1, 3, factory)
	var first: Controller = created[2][0]
	var removed: Controller = created[3][0]
	first.callback = func() -> void:
		instances.synchronize(pair, 2, 4, factory)
		instances.synchronize(pair, 1, 4, factory)
	instances.dispatch(["a", "b"], 4)
	assert(first.ticks == 1)
	assert(removed.ticks == 0)
	assert(created.size() == 6)
	assert(created[5][0].ticks == 0)
	instances.dispatch(["b", "a"], 5)
	assert(created[4][0].ticks == 1 and created[5][0].ticks == 1)
	first.callback = Callable()
	instances.clear()
	print("AI_INSTANCES_SMOKE_OK")
	quit()
