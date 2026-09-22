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
var failed := false
var drive_source_timers := false
var _source_timer_id: int = -1
var _source_timer_elapsed_ms: float = 0.0
var _source_timer_registered_this_tick := false
var callback_events: Array = []
var callback_target_frames: Dictionary = {}
var callback_target_slots: Dictionary = {}
var required_callback_frames: Dictionary = {}
var observed_callback_frames: Dictionary = {}
var clip_target_specs: Dictionary = {}
var clip_target_paths: Dictionary = {}
var clip_callback_events: Array = []
var clip_lifetime_events: Array = []
var clip_live_instances: Dictionary = {}
var clip_traced_registry
var clip_registry_install_audit: Dictionary = {}
var real_wall_clock_step_seconds := 0.0
var real_wall_clock_origin_usec := -1
var current_fixture_tick := -1

func _on_callback(frame: int, entering: bool, fighter: FighterRuntime) -> void:
	if callback_target_frames.has(frame):
		if callback_target_slots.has(frame) and not callback_target_slots[frame].has(fighter.player_slot):
			return
		if entering and required_callback_frames.has(frame):
			observed_callback_frames[frame] = true
		var event := {"slot": fighter.player_slot, "source_frame": frame, "entering": entering, "current_frame": fighter.current_source_frame(), "action": fighter.ai_source_state.read_field("动作"), "ql": fighter.energy, "tick": game.physics_tick, "fixture_tick": current_fixture_tick}
		callback_events.append(event)
		print("LEE_EXACT_CALLBACK ", JSON.stringify(event))

func _on_real_countdown_timer_timeout() -> void:
	print("LEE_REAL_COUNTDOWN_TIMER_FIRE ", JSON.stringify({
		"physics_tick": game.physics_tick,
		"session": game.session.root_label,
		"gametime": game.countdown.locals.get("tm", -1),
		"p1_frame": game.naruto.current_source_frame(),
		"p2_frame": game.ichigo.current_source_frame(),
		"p1_health": game.naruto.health,
		"p2_health": game.ichigo.health,
		"p1_sw": game.naruto.sw,
		"p2_sw": game.ichigo.sw,
		"paused": game.naruto.root_zhanting
	}))

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	var is_batch := args.size() >= 3 and args[0] == "--batch"
	var output_directory := str(args[2]) if is_batch else str(args[1]).get_base_dir()
	if not output_directory.is_empty():
		DirAccess.make_dir_recursive_absolute(output_directory)
	if not output_directory.is_empty() and not DirAccess.dir_exists_absolute(output_directory):
		push_error("Could not create callback probe output directory: %s" % output_directory)
		failed = true
		quit(2)
		return
	if args[0] == "--batch":
		var paths: Array = JSON.parse_string(FileAccess.get_file_as_string(args[1]))
		for path in paths:
			var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
			await _run_case(path, args[2].path_join(str(spec.id) + ".json"))
		print("MOVE_CASE_BATCH_OK ", paths.size())
	else:
		await _run_case(args[0], args[1])
	quit(2 if failed else 0)


func _run_case(fixture_path: String, output_path: String) -> void:
	rows = []
	helper_rows = []
	presentation_rows = []
	recovery_events = {}
	intervention_rows = []
	applied_interventions = {}
	fixture = JSON.parse_string(FileAccess.get_file_as_string(fixture_path))
	callback_events = []
	clip_target_specs = {}
	clip_target_paths = {}
	clip_callback_events = []
	clip_lifetime_events = []
	clip_live_instances = {}
	clip_traced_registry = null
	clip_registry_install_audit = {}
	callback_target_frames = {29: true, 1017: true}
	callback_target_slots = {}
	required_callback_frames = {}
	observed_callback_frames = {}
	for target in fixture.get("source_callback_targets", []):
		if target is Dictionary and target.has("source_frame"):
			var source_frame := int(target.source_frame)
			if str(target.get("kind", "frame_action")) == "clip_action":
				var source_path := str(target.get("source_path", ""))
				assert(not source_path.is_empty(), "Clip target must identify its authored source path")
				clip_target_specs[source_frame] = target.duplicate(true)
				clip_target_paths[source_path] = target.duplicate(true)
				continue
			callback_target_frames[source_frame] = true
			required_callback_frames[source_frame] = true
			if target.has("slot"):
				if not callback_target_slots.has(source_frame):
					callback_target_slots[source_frame] = {}
				callback_target_slots[source_frame][str(target.slot)] = true
	drive_source_timers = bool(fixture.get("drive_source_timers", false))
	real_wall_clock_step_seconds = 0.0
	if fixture.get("real_wall_clock_per_fight_tick", false):
		var execution_profile: Dictionary = JSON.parse_string(
			FileAccess.get_file_as_string("res://generated/main/execution_profile.json"))
		var host_fps := float(execution_profile.get("host_fps", 0.0))
		assert(host_fps > 0.0, "Real-clock fixture requires a measured host_fps")
		real_wall_clock_step_seconds = 1.0 / host_fps
		real_wall_clock_origin_usec = -1
		print("LEE_REAL_CLOCK_PROFILE ", JSON.stringify({
			"host_fps": host_fps,
			"step_seconds": real_wall_clock_step_seconds,
			"profile_id": execution_profile.get("profile_id", "")
		}))
	_source_timer_id = -1
	_source_timer_elapsed_ms = 0.0
	_source_timer_registered_this_tick = false
	_validate_resource_interventions()
	mode = 3
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.recorded_training_timers = true
	if fixture.has("fighters"):
		for helper_key in ["p1_helper", "p2_helper"]:
			if not fixture.has(helper_key) or str(fixture[helper_key]).is_empty():
				push_error("Acceptance fixture must declare %s; implicit helper defaults are invalid" % helper_key)
				failed = true
				return
		var names: Array = []
		for slot in ["p1", "p2"]:
			var display := _fixture_display_id("fighters", str(fixture.fighters[slot]))
			if display.is_empty():
				return
			names.append(display)
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
		game._load_selected_stage(str(fixture.get("stage", "现世")))
	game._enter_current_fight(mode)
	if fixture.get("real_wall_clock_per_fight_tick", false):
		assert(game.countdown != null and game.countdown.timer != null,
			"Real-wall-clock fixture requires the authored match countdown Timer")
		real_wall_clock_origin_usec = Time.get_ticks_usec()
		game.countdown.timer.timeout.connect(_on_real_countdown_timer_timeout)
	game.naruto.source_frame_script_boundary.connect(_on_callback.bind(game.naruto))
	game.ichigo.source_frame_script_boundary.connect(_on_callback.bind(game.ichigo))
	if not clip_target_paths.is_empty():
		_install_clip_callback_observer()
		game.naruto.source_frame_changed.connect(_on_clip_parent_frame_changed.bind(game.naruto))
		game.ichigo.source_frame_changed.connect(_on_clip_parent_frame_changed.bind(game.ichigo))
	for tick in 700:
		game._advance_fight([], func() -> bool:
			if not game.battle_intro.active:
				_drive_source_timers(1000.0 / Engine.physics_ticks_per_second)
				_observe(0)
			return false)
		# The intro can become inactive after the root callback but before the
		# first post-intro observer runs. Keep one more tick so tick 0 retains
		# both fighter snapshots instead of producing an empty trace.
		if not game.battle_intro.active and rows.size() == 2: break
	assert(not game.battle_intro.active and rows.size() == 2)
	for tick in range(1, int(fixture.frames) + 1):
		if game.opponent_driver == null or game.player_body_driver == null:
			print("LEE_FIXTURE_TERMINAL ", JSON.stringify({
				"fixture_tick": tick - 1,
				"physics_tick": game.physics_tick,
				"session": game.session.root_label,
				"observed_callback_frames": observed_callback_frames.keys()
			}))
			break
		current_fixture_tick = tick
		if fixture.get("real_wall_clock_per_fight_tick", false):
			var tick_deadline_usec := real_wall_clock_origin_usec + int(round(
				tick * real_wall_clock_step_seconds * 1000000.0))
			var remaining_usec := tick_deadline_usec - Time.get_ticks_usec()
			if remaining_usec > 0:
				await create_timer(float(remaining_usec) / 1000000.0).timeout
			if tick % 300 == 0:
				print("LEE_REAL_CLOCK_PROGRESS ", JSON.stringify({
					"fight_tick": tick,
					"elapsed_ms": float(Time.get_ticks_usec() - real_wall_clock_origin_usec) / 1000.0,
					"scheduled_elapsed_ms": float(tick_deadline_usec - real_wall_clock_origin_usec) / 1000.0
				}))
		# Timer callbacks occur after the preceding source snapshot and before
		# the next fight advance. Deliver the external clock at that boundary.
		_drive_source_timers(1000.0 / Engine.physics_ticks_per_second)
		game._advance_fight(recovery_events.get(tick, []), func() -> bool:
			_observe(tick)
			return false)
		if game.opponent_driver == null or game.player_body_driver == null:
			print("LEE_FIXTURE_TERMINAL ", JSON.stringify({
				"fixture_tick": tick,
				"physics_tick": game.physics_tick,
				"session": game.session.root_label,
				"observed_callback_frames": observed_callback_frames.keys()
			}))
			break
		if (not fixture.get("capture_callbacks_full_fixture", false)
			and not required_callback_frames.is_empty()
			and observed_callback_frames.size() == required_callback_frames.size()):
			break
	assert(applied_interventions.size() == fixture.get("resource_interventions", []).size(),
		"one or more resource interventions did not execute")
	FileAccess.open(output_path, FileAccess.WRITE).store_string(JSON.stringify(rows, "", true, true))
	FileAccess.open(output_path + ".helpers.json", FileAccess.WRITE).store_string(JSON.stringify(helper_rows, "", true, true))
	FileAccess.open(output_path + ".presentation.json", FileAccess.WRITE).store_string(JSON.stringify(presentation_rows, "", true, true))
	FileAccess.open(output_path + ".interventions.json", FileAccess.WRITE).store_string(JSON.stringify(intervention_rows, "", true, true))
	FileAccess.open(output_path + ".clips.json", FileAccess.WRITE).store_string(JSON.stringify({
		"callback_events": clip_callback_events,
		"lifetime_events": clip_lifetime_events,
		"registry_install_audit": clip_registry_install_audit,
	}, "", true, true))
	game._goto_menu()
	game.queue_free()
	await process_frame
	print("LEE_EXACT_CALLBACK_SUMMARY ", JSON.stringify({"fixture": fixture.id, "events": callback_events}))
	if not clip_target_paths.is_empty():
		print("LEE_CLIP_CALLBACK_SUMMARY ", JSON.stringify({"fixture": fixture.id,
			"callback_events": clip_callback_events, "lifetime_events": clip_lifetime_events}))
	print("MOVE_CASE_REFERENCE_OK ", fixture.id)


func _install_clip_callback_observer() -> void:
	var baseline_registry: SourceCallbackRegistry = game.source_callbacks
	var baseline_snapshot := _clip_registry_snapshot(baseline_registry, false)
	var observed = load("res://tests/callback_trace_registry.gd").new()
	observed.adopt(game.source_callbacks)
	observed.observer = Callable(self, "_on_clip_callback")
	observed.identity_lookup = Callable(self, "_clip_identity_lookup")
	for path in clip_target_paths:
		observed.traced_paths[path] = true
	game.source_callbacks = observed
	clip_traced_registry = observed
	for driver in [game.opponent_driver, game.player_body_driver._driver]:
		driver.callback_registry = observed
		driver.controller.instances.registry = observed
	for helper in [game.naruto_helper, game.ichigo_helper]:
		if helper != null:
			helper._callback_registry = observed
	for timeline in [game.ko_timeline, game.timeout_timeline]:
		if timeline != null:
			timeline.registry = observed
	var observed_snapshot := _clip_registry_snapshot(observed, true)
	clip_registry_install_audit = {
		"baseline": baseline_snapshot,
		"observed": observed_snapshot,
		"same_registration_order_and_placed_tick": baseline_snapshot == observed_snapshot,
	}
	assert(clip_registry_install_audit.same_registration_order_and_placed_tick,
		"test observer changed existing callback registration order or placement phase")


func _clip_registry_snapshot(registry: SourceCallbackRegistry, has_proxies: bool) -> Array:
	var snapshot: Array = []
	for registration in registry._entries.keys():
		var entry: Dictionary = registry._entries[registration]
		var target: Object = entry.target.get_ref()
		var source_path := ""
		if target != null:
			if has_proxies and target.has_method("delegate_alive"):
				var identity: Dictionary = target.get("_identity")
				source_path = str(identity.get("source_path", ""))
			else:
				source_path = str(_clip_identity_lookup(target.get_instance_id()).get("source_path", ""))
		snapshot.append({
			"registration": int(registration),
			"method": str(entry.method),
			"placed_tick": int(entry.placed_tick),
			"source_path": source_path,
		})
	return snapshot


func _clip_identity_lookup(target_instance_id: int) -> Dictionary:
	for actor in [game.naruto, game.ichigo]:
		var driver = game.player_body_driver._driver if actor == game.naruto else game.opponent_driver
		for source_path in driver.controller.instances._instances:
			if not clip_target_paths.has(source_path):
				continue
			var instance: Dictionary = driver.controller.instances._instances[source_path]
			var controller: Object = instance.get("controller")
			if controller == null or controller.get_instance_id() != target_instance_id:
				continue
			var spec: Dictionary = clip_target_paths[source_path]
			var placement := _clip_placement_snapshot(actor, spec)
			return {
				"source_path": source_path,
				"slot": actor.player_slot,
				"generation": int(instance.get("generation", -1)),
				"method": str(instance.get("method", "")),
				"controller_instance_id": target_instance_id,
				"placement": placement,
				"parent_frame_at_registration": actor.current_source_frame(),
			}
	return {}


func _clip_placement_snapshot(actor: FighterRuntime, spec: Dictionary) -> Dictionary:
	var frame := actor.current_source_frame()
	var frame_data: Dictionary = actor._frames.get(frame, {})
	for placement: Dictionary in frame_data.get("display_list", []):
		if int(placement.get("depth", -1)) != int(spec.get("depth", -2)):
			continue
		if int(placement.get("character_id", -1)) != int(spec.get("placement_id", spec.get("controller_id", -2))):
			continue
		if int(placement.get("placed_frame", -1)) != int(spec.get("source_frame", -2)):
			continue
		var definition: Dictionary = actor._definitions.get(int(placement["character_id"]), {})
		var child_frames: Array = definition.get("display_list_frames", [])
		return {
			"depth": int(placement["depth"]),
			"character_id": int(placement["character_id"]),
			"placed_frame": int(placement["placed_frame"]),
			"child_local_frame": actor._nested_frame(placement, frame, child_frames.size()),
			"matrix": placement.get("matrix", {}).duplicate(true),
			"clip_actions": placement.get("clip_actions", []).duplicate(true),
		}
	return {}


func _clip_identity_snapshot(target_instance_id: int) -> Dictionary:
	return _clip_identity_lookup(target_instance_id)


func _on_clip_callback(event: Dictionary) -> void:
	var target_instance_id := int(event.get("controller_instance_id", -1))
	var identity := _clip_identity_snapshot(target_instance_id)
	if identity.is_empty():
		identity = event.duplicate(true)
	var slot := str(identity.get("slot", event.get("slot", "")))
	var actor: FighterRuntime = game.naruto if slot == "p1" else game.ichigo
	var spec: Dictionary = clip_target_paths.get(str(event.get("source_path", "")), {})
	var record := event.duplicate(true)
	record["display_tick"] = int(game.source_callbacks.current_tick)
	record["parent_frame"] = actor.current_source_frame() if actor != null else -1
	record["child_placement"] = _clip_placement_snapshot(actor, spec) if actor != null and not spec.is_empty() else {}
	if actor != null:
		record["parent_x"] = actor.source_x
		record["parent_action"] = actor.ai_source_state.read_field("动作")
		record["parent_ql"] = actor.energy
	clip_callback_events.append(record)
	print("LEE_CLIP_CALLBACK ", JSON.stringify(record))


func _on_clip_parent_frame_changed(_frame: int, actor: FighterRuntime) -> void:
	var slot := str(actor.player_slot)
	var driver = game.player_body_driver._driver if actor == game.naruto else game.opponent_driver
	var live_for_slot := {}
	for source_path in clip_target_paths:
		if not driver.controller.instances._instances.has(source_path):
			continue
		var instance: Dictionary = driver.controller.instances._instances[source_path]
		var controller: Object = instance.get("controller")
		if controller == null:
			continue
		var controller_id := controller.get_instance_id()
		var key := "%s:%s:%d" % [slot, source_path, int(instance.get("generation", -1))]
		live_for_slot[key] = true
		if clip_live_instances.has(key):
			continue
		var spec: Dictionary = clip_target_paths[source_path]
		var registration := int(instance.get("registration", -1))
		var event := {"phase": "placed", "slot": slot, "source_path": source_path,
			"generation": int(instance.get("generation", -1)), "controller_instance_id": controller_id,
			"registration_id": registration, "placed_tick": int(instance.get("placed_tick", -1)),
			"parent_frame": actor.current_source_frame(),
			"placement": _clip_placement_snapshot(actor, spec)}
		clip_live_instances[key] = event
		clip_lifetime_events.append(event)
		print("LEE_CLIP_LIFETIME ", JSON.stringify(event))
	for key in clip_live_instances.keys():
		var prior: Dictionary = clip_live_instances[key]
		if str(prior.get("slot", "")) != slot or live_for_slot.has(key):
			continue
		var event := {"phase": "removed", "slot": slot, "source_path": prior.get("source_path", ""),
			"generation": prior.get("generation", -1), "controller_instance_id": prior.get("controller_instance_id", -1),
			"registration_id": prior.get("registration_id", -1), "placed_tick": prior.get("placed_tick", -1),
			"parent_frame": actor.current_source_frame(), "placement": {}}
		clip_lifetime_events.append(event)
		print("LEE_CLIP_LIFETIME ", JSON.stringify(event))
		clip_live_instances.erase(key)


func _drive_source_timers(delta_ms: float) -> void:
	# The acceptance runner disables SceneTree physics and advances the source
	# clock explicitly. When a fixture opts in, deliver registered source Timer
	# callbacks by their authored wait_time instead of a fixture-specific tick.
	if not drive_source_timers or game == null:
		return
	if game.ko_nextfight_timer == null:
		if _source_timer_id >= 0:
			print("SOURCE_TIMER_CANCEL id=", _source_timer_id,
				" elapsed_ms=", _source_timer_elapsed_ms)
		_source_timer_id = -1
		_source_timer_elapsed_ms = 0.0
		_source_timer_registered_this_tick = false
		return
	var timer: Timer = game.ko_nextfight_timer
	var id := timer.get_instance_id()
	if id != _source_timer_id:
		_source_timer_id = id
		_source_timer_elapsed_ms = 0.0
		# SceneTree physics is disabled by this runner; freeze the real Timer so
		# only the authored source-clock deadline below can deliver the callback.
		timer.paused = true
		print("SOURCE_TIMER_REGISTER id=", id, " wait_ms=", timer.wait_time * 1000.0)
		# Registration starts the authored interval immediately; the current
		# fight boundary contributes to the external source clock.
		_source_timer_registered_this_tick = false
	if timer.is_stopped():
		return
	var elapsed := _source_timer_elapsed_ms + delta_ms
	while elapsed + 0.00001 >= timer.wait_time * 1000.0:
		elapsed -= timer.wait_time * 1000.0
		var before_frame := int(game.ko_timeline.root_clip.frame) if game.ko_timeline != null else -1
		print("SOURCE_TIMER_FIRE ", JSON.stringify({
			"id": id, "deadline_ms": timer.wait_time * 1000.0,
			"physics_tick": game.physics_tick, "session": game.session.root_label,
			"ko_active": game.ko_active, "ko_paused": game.ko_paused,
			"ko_frame": before_frame, "p1_frame": game.naruto.current_source_frame(),
			"p2_frame": game.ichigo.current_source_frame(), "p1_sw": game.naruto.sw,
			"p2_sw": game.ichigo.sw}))
		timer.timeout.emit()
		print("SOURCE_TIMER_AFTER ", JSON.stringify({
			"id": id, "physics_tick": game.physics_tick,
			"session": game.session.root_label,
			"ko_active": game.ko_active, "ko_paused": game.ko_paused,
			"ko_frame": int(game.ko_timeline.root_clip.frame) if game.ko_timeline != null else -1,
			"p1_frame": game.naruto.current_source_frame(), "p2_frame": game.ichigo.current_source_frame(),
			"p1_sw": game.naruto.sw, "p2_sw": game.ichigo.sw}))
		if game.ko_nextfight_timer == null or not is_instance_valid(timer):
			break
	_source_timer_elapsed_ms = elapsed


func _fixture_display_id(kind: String, fixture_id: String) -> String:
	var available: Dictionary = game.character_selection.available[kind]
	for display_id in available:
		if str(available[display_id]) == fixture_id:
			return str(display_id)
	var directory := "res://generated/%s/%s" % [kind, fixture_id]
	var metadata_path := directory.path_join("fighter.json" if kind == "fighters" else "combat.json")
	var timeline_path := directory.path_join("timeline.json")
	var assets_path := directory.path_join("assets.json")
	if not FileAccess.file_exists(metadata_path):
		push_error("Missing fixture metadata: " + metadata_path)
		failed = true
		return ""
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
		if not FileAccess.file_exists(intro_path):
			push_error("Missing fixture opening metadata: " + intro_path)
			failed = true
			return ""
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
			_apply_source_state_preconditions(actor)
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
			"action": helper.source_action, "visible": helper.visible,
			"root_paused": helper.owner_fighter.root_zhanting if is_instance_valid(helper.owner_fighter) else false,
			"parent_frame": helper.owner_fighter.current_source_frame() if is_instance_valid(helper.owner_fighter) else -1,
			"atm1": helper.instance_clip_frame("atm1"), "atm2": helper.instance_clip_frame("atm2"),
			"atm3": helper.instance_clip_frame("atm3")})
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
	var preconditions: Variant = fixture.get("source_state_preconditions", {})
	assert(preconditions is Dictionary, "source_state_preconditions must be an object")
	for slot in preconditions:
		assert(str(slot) in ["p1", "p2"], "source state precondition slot must be p1 or p2")
		assert(preconditions[slot] is Dictionary, "source state precondition must be an object")
		for field in preconditions[slot]:
			assert(str(field) in ["health", "wudi"], "unsupported source state precondition: " + str(field))
			var value: Variant = preconditions[slot][field]
			if field == "health":
				assert(value is int or value is float, "health precondition must be numeric")
			else:
				assert(value is bool, "wudi precondition must be boolean")


func _apply_source_state_preconditions(actor: FighterRuntime) -> void:
	var slot := str(actor.player_slot)
	var preconditions: Dictionary = fixture.get("source_state_preconditions", {}).get(slot, {})
	for field in preconditions:
		var value: Variant = preconditions[field]
		var previous: Variant = actor.health if field == "health" else actor.ai_source_state.read_field(str(field))
		if field == "health":
			actor.health = float(value)
		else:
			actor.ai_source_state.apply_write({"field": str(field), "value": value})
		intervention_rows.append({"id": "source_state:%s:%s" % [slot, field], "tick": 0,
			"slot": slot, "resource": str(field), "previous": previous, "value": value,
			"phase": "source_state_precondition_before_first_observation"})


func _apply_resource_interventions(tick: int) -> void:
	for intervention: Dictionary in fixture.get("resource_interventions", []):
		if int(intervention.tick) != tick:
			continue
		var intervention_id := str(intervention.id)
		assert(not applied_interventions.has(intervention_id), "resource intervention executed twice: " + intervention_id)
		var actor: FighterRuntime = game.naruto if str(intervention.slot) == "p1" else game.ichigo
		var previous: float = float(actor.energy)
		actor.energy = float(intervention.value)
		applied_interventions[intervention_id] = true
		intervention_rows.append({"id": intervention_id, "tick": tick, "slot": intervention.slot,
			"resource": intervention.resource, "previous": previous, "value": actor.energy,
			"phase": "after_actor_advance_before_root_observation_and_next_tick_input"})
