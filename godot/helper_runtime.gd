class_name HelperRuntime
extends TimelinePreview

@export var helper_directory: String

var helper_id: String
var attacking: bool = false
var facing: int = 1
var owner_fighter: FighterRuntime
var last_event: String = "ready"

var _combat: Dictionary
var _hit_instances: Dictionary = {}


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
	show_collision_shapes = true


func activate(spawn: Dictionary, caster: FighterRuntime) -> void:
	# Source yfgj(): place behind the caster, face the opponent, gotoAndPlay(2).
	# Frame 1 display list is empty; start_frame 2 is the first visible frame.
	_ensure_timeline_loaded()
	owner_fighter = caster
	attacking = true
	visible = true
	_hit_instances.clear()
	_reset_preview_offsets()
	position = Vector2(float(spawn.get("x", -200.0)), float(spawn.get("y", -200.0)))
	set_facing(int(spawn.get("facing", 1)))
	var start_frame := int(spawn.get("start_frame", _combat.get("start_frame", 2)))
	play_source_frame(start_frame)
	last_event = "helper_activate_%s" % helper_id
	print("COMBAT_EVENT ", JSON.stringify(snapshot()))


func deactivate() -> void:
	# Source frame_1 parks the clip at (-200, -200) and stop().
	attacking = false
	visible = false
	position = Vector2(-200.0, -200.0)
	_hit_instances.clear()
	play_source_frame(1)
	last_event = "helper_hide_%s" % helper_id


func advance_timeline() -> void:
	if not attacking:
		return
	var end_frame := int(_combat.get("end_frame", current_source_frame()))
	if current_source_frame() >= end_frame:
		deactivate()
		return
	play_source_frame(current_source_frame() + 1)


func enter_frame() -> void:
	if not attacking:
		return
	_aim_atm1_at_opponent()
	for event: Dictionary in _combat.get("drain_events", []):
		if int(event["frame"]) != current_source_frame():
			continue
		if owner_fighter != null and is_instance_valid(owner_fighter.opponent):
			owner_fighter.opponent.change_energy(float(event["delta"]))
			last_event = "helper_drain_%s" % helper_id
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
	_hit_instances[str(attack["instance_name"])] = true
	last_event = "helper_hit_%s" % attack.get("instance_name", "unknown")


func attack_contact(defender: FighterRuntime) -> Dictionary:
	if not attacking or not has_visual_timeline():
		return {}
	var body := defender.instance_global_bounds("bdmn")
	if not body.has_area():
		return {}
	for instance_name in _combat.get("attacks", {}).keys():
		if _hit_instances.has(instance_name):
			continue
		var attack_bounds := instance_global_bounds(instance_name)
		if attack_bounds.has_area() and body.intersects(attack_bounds):
			var attack: Dictionary = _combat["attacks"][instance_name].duplicate(true)
			attack["instance_name"] = instance_name
			return attack
	return {}


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
	set_instance_local_offset("atm1", Vector2.ZERO)


func _aim_atm1_at_opponent() -> void:
	# Source: scripts/fighter/fz/woailuo.json
	# frame_44/PlaceObject2_48_2/CLIPACTIONRECORD onClipEvent(load).as
	# assigns clip._X (replaces PlaceObject translateX) toward the opponent.
	if current_source_frame() != 44:
		return
	if owner_fighter == null or not is_instance_valid(owner_fighter.opponent):
		return
	var placed := named_instance_origin("atm1")
	if placed == Vector2.INF:
		return
	var delta_x := owner_fighter.opponent.position.x - position.x
	var local_x := -delta_x if scale.x < 0.0 else delta_x
	set_instance_local_offset("atm1", Vector2(local_x - placed.x, 0.0))
	refresh_display()
