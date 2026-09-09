extends SceneTree

class Adapter extends RefCounted:
	var state: Dictionary = {}
	var events: Array = []
	func read(key: String) -> Variant:
		assert(state.has(key), "Missing KO fixture field: " + key)
		return state[key]
	func write(key: String, value: Variant) -> void:
		state[key] = value
		events.append(["write", key, value])
	func goto_clip(target: String, label: Variant, playing: bool) -> void:
		events.append(["goto", target, label, playing])
	func set_playing(target: String, playing: bool) -> void:
		events.append(["playing", target, playing])
	func call_root(name: String) -> void:
		events.append(["root", name])
	func register_interval(name: String, delay: int) -> int:
		events.append(["interval", name, delay])
		return 42


func _initialize() -> void:
	var controller = load("res://generated/main/ko/controller.gd").new()
	var adapter := Adapter.new()
	controller.adapter = adapter
	var metadata: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/ko/controller.json"))
	var methods := {}
	for event: Dictionary in metadata.events:
		methods[event.path] = event.method
	for health: Array in [[1000, 0], [0, 1000], [0, 0], [500, 500], [500, 400]]:
		adapter.state = {"_root.game.p1.mc.hp": health[0], "_root.game.p2.mc.hp": health[1], "_root.p1ws": 0, "_root.p2ws": 0, "_root.maxhp": 1000, "_currentframe": 1}
		adapter.events.clear()
		controller.call(methods["DefineSprite_1858/frame_84/DoAction.as"])
		assert(adapter.events == [["goto", "this", "drawgame" if health[0] == health[1] else "winner", false], ["playing", "this", true]])
		adapter.events.clear()
		controller.call(methods["DefineSprite_1858/frame_94/DoAction.as"])
		var winner := "p1" if health[0] > health[1] else "p2"
		assert(adapter.state["_root." + winner + "ws"] == 1)
		assert(adapter.state["_root.焦点"] == winner)
		assert(adapter.state["winmc._x"] == (0 if winner == "p1" else 120))
		adapter.events.clear()
		controller.call(methods["DefineSprite_1844/frame_49/DoAction.as"])
		controller.call(methods["DefineSprite_1844/frame_50/DoAction.as"])
		assert(adapter.events == [["goto", "_root.game." + winner + ".mc", "胜利", true], ["goto", "_root.game." + winner + ".mc", "胜利", true], ["playing", "this", false]])
		adapter.events.clear()
		var perfect_method: String = methods["DefineSprite_1844/frame_20/PlaceObject2_1843_1/CLIPACTIONRECORD onClipEvent(enterFrame).as"]
		controller.call(perfect_method)
		assert(adapter.events.size() == (1 if (health[0] if winner == "p1" else health[1]) == 1000 else 0))
		adapter.state["_currentframe"] = 15
		adapter.events.clear()
		controller.call(perfect_method)
		assert(adapter.events.is_empty())
	for side in [1, 2]:
		for mode in [1, 2, 3]:
			adapter.state = {"_root.p1ws": 3 if side == 1 else 0, "_root.p2ws": 3 if side == 2 else 0, "_root.modo": mode, "_root.maxtime": 99}
			adapter.events.clear()
			controller.call(methods["DefineSprite_1858/frame_394/DoAction.as"])
			assert(adapter.state["_root.gametime"] == 99)
			var target := "选人画面" if mode != 1 else ("YOUWIN" if side == 1 else "继续")
			assert(adapter.events.slice(1) == [["root", "clearint"], ["goto", "_root", target, false]])
	adapter.state = {"_root.p1ws": 2, "_root.p2ws": 2, "_root.maxtime": 99, "_root.rounds": 2}
	adapter.events.clear()
	controller.call(methods["DefineSprite_1858/frame_394/DoAction.as"])
	assert(adapter.events[1] == ["interval", "nextfight", 1000])
	assert(adapter.state["_root.nxtfht"] == 42)
	adapter.events.clear()
	controller.nextfight()
	assert(adapter.state["_root.rounds"] == 3)
	assert(adapter.events[4] == ["root", "chushi"])
	assert(adapter.events[-1] == ["playing", "_root.ready", true])
	assert(adapter.state["_root.game.p1.mc.sw"] == false)
	assert(adapter.state["_root.game.p2.mc.sw"] == false)
	print("KO_CONTROLLER_SMOKE_OK")
	quit()
