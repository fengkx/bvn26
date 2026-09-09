class_name HelperRuntime
extends TimelinePreview

signal effect_requested(clip_name: String, source_position: Vector2, source_facing: int, offset_y: float)

@export var helper_directory: String

var helper_id: String
var attacking: bool = false
var facing: int = 1
var owner_fighter: FighterRuntime
var last_event: String = "ready"
var timeline_playing: bool = true
var bs: int = 0
var hited: int = 0
var sw: bool = false
var source_action: Variant = null

var _combat: Dictionary
var _events_applied: Dictionary = {}


func _ready() -> void:
	autoplay = false
	if fighter_directory == "" and helper_directory != "":
		fighter_directory = helper_directory
	super._ready()
	_combat = _read_json("%s/combat.json" % helper_directory)
	helper_id = str(_combat.get("helper_id", "helper"))
	# Source woailuo frame_1/DoAction.as: _X = _Y = -200; stop();
	visible = false
	position = Vector2(-200.0, -200.0)


func activate(spawn: Dictionary, caster: FighterRuntime) -> void:
	# Source yfgj(): place behind the caster, face the opponent, gotoAndPlay(2).
	# Frame 1 display list is empty; start_frame 2 is the first visible frame.
	_ensure_timeline_loaded()
	owner_fighter = caster
	attacking = true
	timeline_playing = true
	visible = true
	_events_applied.clear()
	_reset_preview_offsets()
	position = Vector2(float(spawn.get("x", -200.0)), float(spawn.get("y", -200.0)))
	set_facing(int(spawn.get("facing", 1)))
	var start_frame := int(spawn.get("start_frame", _combat.get("start_frame", 2)))
	play_source_frame(start_frame)
	_apply_frame_events()
	last_event = "helper_activate_%s" % helper_id
	print("COMBAT_EVENT ", JSON.stringify(snapshot()))


func deactivate() -> void:
	# Source frame_1 parks the clip at (-200, -200) and stop().
	attacking = false
	# main frame_8 removeFZ explicitly clears mc.动作.
	source_action = 0
	bs = 0
	timeline_playing = true
	visible = false
	position = Vector2(-200.0, -200.0)
	play_source_frame(1)
	last_event = "helper_hide_%s" % helper_id


func advance_timeline() -> void:
	if not attacking or not timeline_playing:
		return
	var end_frame := int(_combat.get("end_frame", current_source_frame()))
	if current_source_frame() >= end_frame:
		deactivate()
		return
	play_source_frame(current_source_frame() + 1)


func enter_frame() -> void:
	if not attacking:
		return
	_apply_frame_events()
	for hide_frame in _combat.get("hide_frames", []):
		if int(hide_frame) == current_source_frame():
			deactivate()
			return


func has_visual_timeline() -> bool:
	return not _frames.is_empty()


func visual_child_count() -> int:
	var count := 0
	for child in get_children():
		if child is Sprite2D:
			count += 1
	return count


func instance_placed_origin(instance_name: String) -> Vector2:
	return named_instance_origin(instance_name)


func apply_attack_contact(attack: Dictionary, defender: FighterRuntime) -> void:
	defender.receive_attack(attack, facing)
	last_event = "helper_hit_%s" % attack.get("instance_name", "unknown")


func attack_contact(defender: FighterRuntime) -> Dictionary:
	if not attacking or not has_visual_timeline():
		return {}
	if not defender.allows_source_hit():
		return {}
	var body := defender.instance_global_bounds("bdmn")
	if not body.has_area():
		return {}
	for instance_name in _combat.get("attacks", {}).keys():
		var attack_bounds := instance_global_bounds(instance_name)
		if attack_bounds.has_area() and SourceHitTest.intersects(body, attack_bounds):
			var attack: Dictionary = _combat["attacks"][instance_name].duplicate(true)
			attack["instance_name"] = instance_name
			return attack
	return {}


func _nested_frame(placement: Dictionary, timeline_frame: int, frame_count: int, clip_age: int = 0) -> int:
	# A terminal stop belongs to the child timeline, even while its parent plays.
	for event: Dictionary in _combat.get("nested_stops", []):
		if int(event["sprite_id"]) == int(placement["character_id"]):
			var age := maxi(0, timeline_frame - int(placement.get("placed_frame", timeline_frame)))
			return mini(age + 1, int(event["frame"]))
	return super._nested_frame(placement, timeline_frame, frame_count, clip_age)


func set_facing(value: int) -> void:
	if value == 0:
		return
	facing = signi(value)
	scale.x = absf(scale.x) * facing


func snapshot() -> Dictionary:
	return {
		"helper": helper_id,
		"frame": current_source_frame(),
		"x": position.x,
		"y": position.y,
		"facing": facing,
		"attacking": attacking,
		"event": last_event,
	}


func _ensure_timeline_loaded() -> void:
	if helper_directory != "" and fighter_directory != helper_directory:
		fighter_directory = helper_directory
	if not _frames.is_empty():
		return
	_load_data()


func _reset_preview_offsets() -> void:
	_instance_local_offsets.clear()


func _apply_frame_events() -> void:
	var frame := current_source_frame()
	if _events_applied.has(frame):
		return
	_events_applied[frame] = true
	for event: Dictionary in _combat.get("action_events", []):
		if int(event["frame"]) == frame:
			source_action = event["value"]
	for event: Dictionary in _combat.get("clip_load_events", []):
		if int(event["frame"]) == frame:
			_aim_placed_clip(event)
	for event: Dictionary in _combat.get("drain_events", []):
		if int(event["frame"]) != current_source_frame():
			continue
		if owner_fighter != null and is_instance_valid(owner_fighter.opponent):
			owner_fighter.opponent.change_energy(float(event["delta"]))
			last_event = "helper_drain_%s" % helper_id
	if owner_fighter == null:
		return
	var runtime: SuperRuntime = owner_fighter.super_runtime
	for event: Dictionary in _combat.get("presentation_events", []):
		if int(event["frame"]) != frame:
			continue
		match str(event["op"]):
			"effect":
				effect_requested.emit(str(event["xg"]), position, facing, 0.0)
			"shine":
				if runtime != null:
					runtime.shine_requested.emit(int(event["color"]))
			_:
				if runtime != null:
					runtime.apply(event, owner_fighter, owner_fighter.opponent, owner_fighter.super_helpers)


func _aim_placed_clip(event: Dictionary) -> void:
	if event.get("op") != "aim_opponent_x" or not is_instance_valid(owner_fighter):
		return
	if not is_instance_valid(owner_fighter.opponent):
		return
	for placement: Dictionary in _frames[current_source_frame()]["display_list"]:
		if int(placement["depth"]) != int(event["depth"]):
			continue
		if int(placement["character_id"]) != int(event["character_id"]):
			continue
		var instance_name := str(placement["name"])
		var placed := named_instance_origin(instance_name)
		var delta_x := owner_fighter.opponent.position.x - position.x
		var local_x := -delta_x if scale.x < 0.0 else delta_x
		set_instance_local_offset(instance_name, Vector2(local_x - placed.x, 0.0))
		refresh_display()
