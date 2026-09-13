extends SceneTree

var game
var fixture: Dictionary
var mode: int
var rows: Array = []
var helper_rows: Array = []
var presentation_rows: Array = []
var recovery_events: Dictionary = {}
var intervention_rows: Array = []
var applied_interventions: Dictionary = {}

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args[0] == "--batch":
		var paths: Array = JSON.parse_string(FileAccess.get_file_as_string(args[1]))
		for path in paths:
			var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
			await _run_case(path, args[2].path_join(str(spec.id) + ".json"))
		print("MOVE_CASE_BATCH_OK ", paths.size())
	else:
		await _run_case(args[0], args[1])
	quit()


func _run_case(fixture_path: String, output_path: String) -> void:
	rows = []
	helper_rows = []
	presentation_rows = []
	recovery_events = {}
	intervention_rows = []
	applied_interventions = {}
	fixture = JSON.parse_string(FileAccess.get_file_as_string(fixture_path))
	_validate_resource_interventions()
	mode = 3
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.recorded_training_timers = true
	if fixture.has("fighters"):
		var names: Array = []
		for slot in ["p1", "p2"]:
			names.append(_fixture_display_id("fighters", str(fixture.fighters[slot])))
		var helpers := ["我爱罗", "魂"]
		for index in 2:
			var key := "p%d_helper" % (index + 1)
			if not fixture.has(key):
				continue
			var requested := str(fixture[key])
			var helper_name := ""
			for display_name in game.character_selection.available.helpers:
				if display_name == requested or str(game.character_selection.available.helpers[display_name]) == requested:
					helper_name = display_name
					break
			if helper_name.is_empty():
				helper_name = _fixture_display_id("helpers", requested)
			helpers[index] = helper_name
		game._replace_selected_actors(names, helpers)
		game._load_selected_stage("现世")
	game._enter_current_fight(mode)
	for tick in 700:
		game._advance_fight([], func() -> bool:
			if not game.battle_intro.active: _observe(0)
			return false)
		if not game.battle_intro.active: break
	assert(not game.battle_intro.active and rows.size() == 2)
	for tick in range(1, int(fixture.frames) + 1):
		game._advance_fight(recovery_events.get(tick, []), func() -> bool:
			_observe(tick)
			return false)
	assert(applied_interventions.size() == fixture.get("resource_interventions", []).size(),
		"one or more resource interventions did not execute")
	FileAccess.open(output_path, FileAccess.WRITE).store_string(JSON.stringify(rows, "", true, true))
	FileAccess.open(output_path + ".helpers.json", FileAccess.WRITE).store_string(JSON.stringify(helper_rows, "", true, true))
	FileAccess.open(output_path + ".presentation.json", FileAccess.WRITE).store_string(JSON.stringify(presentation_rows, "", true, true))
	FileAccess.open(output_path + ".interventions.json", FileAccess.WRITE).store_string(JSON.stringify(intervention_rows, "", true, true))
	game._goto_menu()
	game.queue_free()
	await process_frame
	print("MOVE_CASE_REFERENCE_OK ", fixture.id)


func _fixture_display_id(kind: String, fixture_id: String) -> String:
	var available: Dictionary = game.character_selection.available[kind]
	for display_id in available:
		if str(available[display_id]) == fixture_id:
			return str(display_id)
	var directory := "res://generated/%s/%s" % [kind, fixture_id]
	var metadata_path := directory.path_join("fighter.json" if kind == "fighters" else "combat.json")
	var timeline_path := directory.path_join("timeline.json")
	var assets_path := directory.path_join("assets.json")
	assert(FileAccess.file_exists(metadata_path), "Missing fixture metadata: " + metadata_path)
	assert(FileAccess.file_exists(timeline_path), "Missing fixture timeline: " + timeline_path)
	assert(FileAccess.file_exists(assets_path), "Missing fixture assets: " + assets_path)
	var metadata: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(metadata_path))
	var timeline: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(timeline_path))
	var assets: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(assets_path))
	var display_id := str(metadata.get("fighter_id" if kind == "fighters" else "helper_id", ""))
	assert(not display_id.is_empty(), "Missing source display id: " + metadata_path)
	var source_swf: Dictionary = timeline.get("source_swf", {})
	var source_path := str(source_swf.get("path", ""))
	assert(source_path.get_file().get_basename().to_lower() == fixture_id.to_lower(),
		"Fixture id/source SWF mismatch: %s != %s" % [fixture_id, source_path])
	var source_file := "res://../" + source_path
	assert(FileAccess.file_exists(source_file), "Missing frozen fixture source: " + source_file)
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://../manifest.json"))
	var expected_sha := str(manifest.get("file_sha256", {}).get(source_path, ""))
	assert(not expected_sha.is_empty() and expected_sha == str(source_swf.get("sha256", "")),
		"Fixture source hash/manifest mismatch: " + source_path)
	assert(FileAccess.get_sha256(source_file) == expected_sha,
		"Fixture source hash differs from the frozen input: " + source_path)
	if kind == "fighters" and not game.battle_intro.spec["fighters"].has(fixture_id):
		var intro_path := directory.path_join("intro.json")
		assert(FileAccess.file_exists(intro_path), "Missing fixture opening metadata: " + intro_path)
		var intro: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(intro_path))
		assert(str(intro.get("fighter_id", "")) == fixture_id,
			"Fixture id/opening metadata mismatch: " + fixture_id)
		assert(int(intro.get("source_sprite_id", -1)) == int(timeline.get("sprite_id", -2)),
			"Fixture timeline/opening sprite mismatch: " + fixture_id)
		game.battle_intro.spec["fighters"][fixture_id] = {"state_frames": intro.get("state_frames", {})}
	assert(not assets.get("assets", []).is_empty(), "No materialized source assets: " + assets_path)
	for asset in assets.assets:
		var asset_path := directory.path_join(str(asset.get("path", "")))
		assert(FileAccess.file_exists(asset_path), "Missing materialized asset: " + asset_path)
	assert(not available.has(display_id) or str(available[display_id]) == fixture_id,
		"Fixture display id conflicts with the existing roster: " + display_id)
	available[display_id] = fixture_id
	return display_id

func _observe(tick: int) -> void:
	_apply_resource_interventions(tick)
	presentation_rows.append({"tick": tick, "x": game.position.x, "y": game.position.y})
	if tick == 0:
		for actor in [game.naruto, game.ichigo]:
			var setup: Dictionary = fixture.setup[actor.player_slot]
			actor.goto_ai_label("站立", true)
			actor.position.x = setup.x
			actor.energy = setup.energy
	for actor in [game.naruto, game.ichigo]:
		rows.append({"tick": tick, "slot": actor.player_slot, "frame": actor.current_source_frame(),
			"x": actor.source_x, "y": actor.source_y, "xscale": actor.scale.x * 100,
			"action": actor.ai_source_state.read_field("动作"), "hp": actor.health,
			"ql": actor.energy, "sw": actor.sw, "touch": actor.ai_source_state.read_field("touch"),
			"touchFloor": actor.ai_source_state.read_field("touchFloor"), "hits": actor.hits,
			"paused": actor.root_zhanting, "hstm": actor.ai_source_state.read_field("hstm"),
			"hurtSkling": actor.ai_source_state.read_field("hurtSkling")})
	for helper in [game.naruto_helper, game.ichigo_helper]:
		helper_rows.append({"tick": tick, "slot": "p1" if helper == game.naruto_helper else "p2",
			"frame": helper.current_source_frame(), "x": helper.position.x, "y": helper.position.y,
			"facing": helper.facing, "attacking": helper.attacking,
			"action": helper.source_action})
	var bindings := {
		"p1": {"up": KEY_W, "down": KEY_S, "left": KEY_A, "right": KEY_D,
			"attack": KEY_J, "jump": KEY_K, "dash": KEY_L, "ranged": KEY_U, "special": KEY_I, "summon": KEY_O},
		"p2": {"up": KEY_UP, "down": KEY_DOWN, "left": KEY_LEFT, "right": KEY_RIGHT,
			"attack": KEY_KP_1, "jump": KEY_KP_2, "dash": KEY_KP_3, "ranged": KEY_KP_4, "special": KEY_KP_5, "summon": KEY_KP_6}}
	var held := {}
	for item in fixture.inputs:
		if tick >= int(item.start) and tick < int(item.end):
			for key in item["keys"]: held[bindings[item.slot][key]] = true
	for slot in bindings.values():
		for key in slot.values():
			var event := InputEventKey.new()
			event.keycode = key
			event.physical_keycode = key
			event.pressed = held.has(key)
			Input.parse_input_event(event)
	Input.flush_buffered_events()


func _validate_resource_interventions() -> void:
	var interventions: Variant = fixture.get("resource_interventions", [])
	assert(interventions is Array, "resource_interventions must be an array")
	var ids: Dictionary = {}
	for intervention: Variant in interventions:
		assert(intervention is Dictionary, "resource intervention must be an object")
		var intervention_id := str(intervention.get("id", ""))
		var tick := int(intervention.get("tick", 0))
		var slot := str(intervention.get("slot", ""))
		var resource := str(intervention.get("resource", ""))
		var value: Variant = intervention.get("value")
		assert(not intervention_id.is_empty() and not ids.has(intervention_id), "resource intervention id must be unique")
		assert(tick >= 1 and tick <= int(fixture.get("frames", 0)), "resource intervention tick is out of range")
		assert(slot in ["p1", "p2"] and resource == "energy", "unsupported resource intervention")
		assert(value is int or value is float, "resource intervention value must be numeric")
		ids[intervention_id] = true


func _apply_resource_interventions(tick: int) -> void:
	for intervention: Dictionary in fixture.get("resource_interventions", []):
		if int(intervention.tick) != tick:
			continue
		var intervention_id := str(intervention.id)
		assert(not applied_interventions.has(intervention_id), "resource intervention executed twice: " + intervention_id)
		var actor: FighterRuntime = game.naruto if str(intervention.slot) == "p1" else game.ichigo
		var previous := actor.energy
		actor.energy = float(intervention.value)
		applied_interventions[intervention_id] = true
		intervention_rows.append({"id": intervention_id, "tick": tick, "slot": intervention.slot,
			"resource": intervention.resource, "previous": previous, "value": actor.energy,
			"phase": "after_actor_advance_before_root_observation_and_next_tick_input"})
