extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var defender := FighterRuntime.new()
	defender.fighter_directory = "res://generated/fighters/minren"
	var attacker := FighterRuntime.new()
	attacker.fighter_directory = "res://generated/fighters/yihu"
	root.add_child(defender)
	root.add_child(attacker)
	await process_frame
	defender.opponent = attacker
	attacker.opponent = defender
	defender.position = Vector2(200.0, 0.0)
	defender.start_action("站立")
	defender.set_facing(1)
	attacker.position = Vector2(250.0, 0.0)
	attacker.start_action("站立")
	attacker.set_facing(-1)
	attacker.energy = 100.0
	attacker.start_action("上必杀")
	while attacker.current_source_frame() < 548:
		attacker.advance_timeline()
	assert(attacker.current_source_frame() == 548)
	var bounds := attacker.instance_global_bounds("sbsatm")
	assert(bounds.has_area())
	assert(bounds.size.x > 140.0 and bounds.size.y < 90.0,
		"Source MATRIX skew order must keep the wide attack in front: %s" % bounds)
	var receiver := defender.instance_global_bounds("bdmn")
	assert(SourceHitTest.intersects(receiver, bounds))
	var contact := attacker.attack_contact(defender)
	assert(contact.get("instance_name") == "sbsatm", "Unexpected source hitbox: %s" % contact)
	attacker.queue_free()
	defender.queue_free()
	await process_frame
	print("SOURCE_ROTATED_COLLISION_SMOKE_OK")
	quit()
