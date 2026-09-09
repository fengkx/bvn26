class_name StageHitRuntime
extends TimelinePreview

var caster: FighterRuntime
var packet: Dictionary
var expired: bool = false
var source_name: String = ""
var _spec: Dictionary


func configure(directory: String, owner_fighter: FighterRuntime, hit: Dictionary) -> void:
	fighter_directory = directory
	caster = owner_fighter
	packet = hit.duplicate(true)
	position = caster.position
	scale.x = caster.scale.x
	autoplay = false
	_spec = _read_json(directory.path_join("stage_hit.json"))
	assert(_spec["format"] == "bvn26-stage-hit-v1")


func advance_timeline() -> void:
	if expired:
		return
	play_source_frame(current_source_frame() + 1)


func run_frame_actions() -> void:
	if current_source_frame() == int(_spec["remove"]["frame"]):
		expired = true
		queue_free()


func attack_contact(defender: FighterRuntime) -> Dictionary:
	if expired or defender == caster or not defender.allows_source_hit():
		return {}
	var attack_bounds := instance_global_bounds(_spec["hit_instance"])
	var body_bounds := defender.instance_global_bounds("bdmn")
	if not attack_bounds.has_area() or not body_bounds.has_area() or not SourceHitTest.intersects(attack_bounds, body_bounds):
		return {}
	# getStgHitObj returns the stored packet on every eligible lookup. There is
	# no per-instance consumed flag here; receiver clip lifetime controls calls.
	return {
		"instance_name": (source_name if source_name != "" else str(name)) + ":" + str(_spec["hit_instance"]),
		"damage": packet["pw"], "impact_strength": packet["zl"],
		"vertical_impulse": packet["yup"], "horizontal_impulse": packet["hitx"],
		"hitstun_ms": packet["hdtime"], "reaction_label": packet["htype"],
	}


func apply_attack_contact(attack: Dictionary, defender: FighterRuntime) -> void:
	# The packet has no direction field. onBeHit/updateDirect reads the current
	# opponent wrapper, independently of the effect's copied visual transform.
	defender.receive_attack(attack, caster.facing)
