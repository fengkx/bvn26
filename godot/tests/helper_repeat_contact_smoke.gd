extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var caster := FighterRuntime.new()
	caster.fighter_directory = "res://generated/fighters/minren"
	var defender := FighterRuntime.new()
	defender.fighter_directory = "res://generated/fighters/yihu"
	var helper := HelperRuntime.new()
	helper.helper_directory = "res://generated/helpers/woailuo"
	root.add_child(caster)
	root.add_child(defender)
	root.add_child(helper)
	caster.opponent = defender
	defender.opponent = caster
	var failed := false
	for direction in [1, -1]:
		helper.activate({"x": 200, "y": 0, "facing": direction}, caster)
		defender.start_action("站立")
		helper.play_source_frame(44)
		defender.position += helper.instance_global_bounds("atm1").get_center() - defender.instance_global_bounds("bdmn").get_center()
		var first := helper.attack_contact(defender)
		assert(not first.is_empty())
		helper.apply_attack_contact(first, defender)
		# The receiver is absent at 738-740; its retained sand must not be consumed.
		assert(helper.attack_contact(defender).is_empty())
		defender.play_source_frame(741)
		assert(not defender.has_active_hit_receiver())
		defender.play_source_frame(742)
		assert(defender.has_active_hit_receiver())
		defender.position += helper.instance_global_bounds("atm1").get_center() - defender.instance_global_bounds("bdmn").get_center()
		if helper.attack_contact(defender).is_empty():
			push_error("Retained helper hitbox was consumed after its first hit")
			failed = true
		defender.root_zhanting = true
		assert(helper.attack_contact(defender).is_empty())
		defender.root_zhanting = false
		for disabled: Variant in [false, null, 0]:
			defender.ai_source_state.values["canhit"] = disabled
			assert(helper.attack_contact(defender).is_empty())
		defender.ai_source_state.values["canhit"] = true
		# Sprite 48 stops on its empty frame 33; it must never wrap to frame 1.
		for frame in range(76, 86):
			helper.play_source_frame(frame)
			if helper.instance_global_bounds("atm1").has_area():
				push_error("Stopped helper sand reappeared at root frame %d" % frame)
				failed = true
		helper.advance_timeline()
		assert(not helper.attacking)
	helper.free()
	helper = HelperRuntime.new()
	helper.helper_directory = "res://generated/helpers/kon"
	root.add_child(helper)
	for direction in [1, -1]:
		helper.activate({"x": 200, "y": 0, "facing": direction}, caster)
		defender.start_action("站立")
		helper.play_source_frame(37)
		defender.position += helper.instance_global_bounds("atm1").get_center() - defender.instance_global_bounds("bdmn").get_center()
		var first := helper.attack_contact(defender)
		assert(not first.is_empty() and first["damage"] == 10)
		helper.apply_attack_contact(first, defender)
		defender.play_source_frame(742)
		helper.play_source_frame(41)
		defender.position += helper.instance_global_bounds("atm1").get_center() - defender.instance_global_bounds("bdmn").get_center()
		if helper.attack_contact(defender).is_empty():
			push_error("Kon MOVE retained a consumed hitbox")
			failed = true
		helper.play_source_frame(65)
		assert(helper.attack_contact(defender).is_empty())
	caster.free()
	defender.free()
	helper.free()
	if not failed:
		print("HELPER_REPEAT_CONTACT_SMOKE_OK")
	quit(1 if failed else 0)
