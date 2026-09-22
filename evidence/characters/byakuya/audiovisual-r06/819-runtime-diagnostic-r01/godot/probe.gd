extends SceneTree

var game: Node
var fight_start := -1

func _initialize() -> void:
	_probe.call_deferred()

func _probe() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 1, "expected output directory")
	var output := str(args[0])
	DirAccess.make_dir_recursive_absolute(output)
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	await process_frame
	game._on_menu_confirmed("vs_com")
	game.character_selection.available.fighters["白哉"] = "byakuya"
	game._on_characters_confirmed(["白哉", "一护"], ["魂", "魂"])
	game._on_map_confirmed("现世")
	game.diagnostic_input_provider = Callable(self, "_input_tape")
	for _tick in 900:
		if not game.battle_intro.active and fight_start < 0:
			fight_start = game.physics_tick
			game.naruto.source_x = 300.0
			game.naruto.source_y = -25.0
			game.ichigo.source_x = 350.0
			game.ichigo.source_y = -25.0
			game.naruto.sync_body_collision_position()
			game.ichigo.sync_body_collision_position()
			game.naruto.energy = 300.0
			game.ichigo.energy = 300.0
		game._advance_fight()
		if fight_start >= 0 and game.naruto.current_source_frame() == 819:
			break
	var payload := {
		"fight_start": fight_start,
		"physics_tick": game.physics_tick,
		"p1": _actor_state(game.naruto),
		"p1_helper": _actor_state(game.naruto_helper),
		"p2_helper": _actor_state(game.ichigo_helper),
		"world": _tree(game.game_world),
		"root": _tree(game),
		"effect_nodes": _effect_nodes(game),
	}
	game._advance_fight()
	payload["one_tick_later"] = {
		"physics_tick": game.physics_tick,
		"p1": _actor_state(game.naruto),
		"p1_helper": _actor_state(game.naruto_helper),
		"effect_nodes": _effect_nodes(game),
	}
	var file := FileAccess.open(output.path_join("runtime-probe.json"), FileAccess.WRITE)
	assert(file != null, "cannot open probe output")
	file.store_string(JSON.stringify(payload, "  ") + "\n")
	file.flush()
	print("BYAKUYA_819_PROBE_WRITTEN ", output.path_join("runtime-probe.json"))
	quit()

func _input_tape(slot: String, tick: int) -> Dictionary:
	var keys := {"up": false, "down": false, "left": false, "right": false,
		"attack": false, "jump": false, "dash": false, "ranged": false,
		"special": false, "summon": false}
	if fight_start >= 0 and slot == "p1":
		var relative := tick - fight_start
		keys["summon"] = relative >= 10 and relative < 13
	return keys

func _actor_state(actor: Node) -> Dictionary:
	if actor == null:
		return {}
	var result := {"name": actor.name, "path": str(actor.get_path()), "class": actor.get_class()}
	for name in ["helper_id", "helper_directory", "source_action", "attacking", "facing", "bs", "hited", "timeline_playing", "_current_frame", "_source_entry_serial", "_activation_generation", "_nested_dispatch_frame", "_instance_local_frames", "_retained_visual_clips"]:
		if _has(actor, name):
			var value = actor.get(name)
			if name in ["_retained_visual_clips"]:
				result[name] = str(value)
			else:
				result[name] = value
	if actor is Node2D:
		result["position"] = {"x": actor.position.x, "y": actor.position.y}
		result["scale"] = {"x": actor.scale.x, "y": actor.scale.y}
	return result

func _has(object: Object, name: String) -> bool:
	for property in object.get_property_list():
		if str(property.get("name", "")) == name:
			return true
	return false

func _tree(node: Node, depth: int = 0) -> Array:
	if node == null or depth > 6:
		return []
	var row := {"name": node.name, "path": str(node.get_path()), "class": node.get_class(), "children": []}
	if node is Node2D:
		row["position"] = {"x": node.position.x, "y": node.position.y}
		row["scale"] = {"x": node.scale.x, "y": node.scale.y}
	if node is CanvasItem:
		row["visible"] = node.visible
		row["z_index"] = node.z_index
	for name in ["_current_frame", "current_source_frame", "source_frame", "local_frame", "character_id", "source_entry_serial", "_directory", "effect_frame", "_frame_count", "auto_advance"]:
		if _has(node, name):
			row[name] = node.get(name)
	for child in node.get_children():
		row["children"].append_array(_tree(child, depth + 1))
	return [row]

func _effect_nodes(node: Node, depth: int = 0) -> Array:
	if node == null or depth > 10:
		return []
	var result: Array = []
	if node.get_class() == "Node2D" and (_has(node, "_directory") or _has(node, "effect_frame")):
		result.append(_actor_state(node))
		result.append_array(_tree(node))
	for child in node.get_children():
		result.append_array(_effect_nodes(child, depth + 1))
	return result
