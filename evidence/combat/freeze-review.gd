# Focused regression probe for both sourced freeze gates.
# Run with Godot --headless --path godot --script ../evidence/combat/freeze-review.gd.
extends SceneTree


func _initialize() -> void:
	run.call_deferred()


func run() -> void:
	var attacker = load("res://fighter_runtime.gd").new()
	attacker.fighter_directory = "res://generated/fighters/minren"
	root.add_child(attacker)
	var defender = load("res://fighter_runtime.gd").new()
	defender.fighter_directory = "res://generated/fighters/yihu"
	root.add_child(defender)
	attacker.opponent = defender
	defender.opponent = attacker
	attacker.player_slot = "p1"
	defender.player_slot = "p2"
	var super_runtime = load("res://super_runtime.gd").new()
	attacker.super_runtime = super_runtime
	defender.super_runtime = super_runtime
	var attack: Dictionary = attacker._combat.attacks.cbs2
	defender.receive_attack(attack, 1)
	super_runtime.apply({"op":"super_start","kind":"cbsd"},attacker,defender)
	var before = defender.position
	var time_before = defender._hurt_motion_ticks
	defender.enter_frame({})
	print("REVIEW_HURT_FREEZE root=",defender.root_zhanting," hited=",defender.hited," before=",before," after=",defender.position," time=",time_before,"->",defender._hurt_motion_ticks)
	var hurt_frozen = defender.position == before and defender._hurt_motion_ticks == time_before
	super_runtime.reset(attacker,defender)
	defender.start_action("站立")
	defender.health = 1000
	var helper = load("res://helper_runtime.gd").new()
	helper.helper_directory = "res://generated/helpers/woailuo"
	root.add_child(helper)
	helper.activate({"x":200,"y":0,"facing":1},attacker)
	helper.play_source_frame(44)
	var helper_bounds = helper.instance_global_bounds("atm1")
	var body_bounds = defender.instance_global_bounds("bdmn")
	defender.position += helper_bounds.get_center() - body_bounds.get_center()
	super_runtime.apply({"op":"super_start","kind":"cbsd"},attacker,defender,[helper])
	var health_before = defender.health
	load("res://combat_resolver.gd").resolve_helpers([helper],[attacker,defender])
	print("REVIEW_HELPER_FREEZE root=",defender.root_zhanting," playing=",helper.timeline_playing," hp=",health_before,"->",defender.health)
	var helper_frozen = defender.health == health_before
	super_runtime.reset(attacker,defender,[helper])
	attacker.free()
	defender.free()
	helper.free()
	quit(0 if hurt_frozen and helper_frozen else 1)
