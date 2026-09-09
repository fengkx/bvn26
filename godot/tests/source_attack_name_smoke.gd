extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var attacker := FighterRuntime.new()
	attacker.fighter_directory = "res://generated/fighters/yihu"
	var defender := FighterRuntime.new()
	defender.fighter_directory = "res://generated/fighters/minren"
	root.add_child(attacker)
	root.add_child(defender)
	attacker.opponent = defender
	defender.opponent = attacker
	attacker.position = Vector2(200, 0)
	attacker.play_source_frame(360)
	var sensor := attacker.instance_global_bounds("zh20atm")
	assert(sensor.has_area())
	defender.position = sensor.get_center() - defender.instance_global_bounds("bdmn").get_center()
	assert(sensor.intersects(defender.instance_global_bounds("bdmn")))
	assert("zh20atm" not in attacker._combat.hit_priority.instances)
	# Sprite 2 queries exact _fsArray names; Sprite 638 uses zh20 only to
	# enter 招21. A spatial overlap with that sensor must not receive damage.
	if not attacker.attack_contact(defender, true).is_empty():
		push_error("Source zh20atm sensor must not alias the zh2atm attack")
		quit(1)
		return
	assert(attacker._attack_from_instance("zh20atm").is_empty())
	assert(attacker._attack_from_instance("zh2atm").damage == 80)
	attacker.queue_free()
	defender.queue_free()
	await process_frame
	print("SOURCE_ATTACK_NAME_SMOKE_OK")
	quit()
