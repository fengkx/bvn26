extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var helper := HelperRuntime.new()
	helper.helper_directory = "res://generated/helpers/you"
	helper.fighter_directory = helper.helper_directory
	var owner := FighterRuntime.new()
	owner.fighter_directory = "res://generated/fighters/kakashi"
	var defender := FighterRuntime.new()
	defender.fighter_directory = "res://generated/fighters/sasuke"
	root.add_child(owner)
	root.add_child(defender)
	root.add_child(helper)
	await process_frame
	owner.opponent = defender
	defender.opponent = owner
	helper.owner_fighter = owner
	helper.position = Vector2(280, -25)
	helper.scale = Vector2.ONE
	var event: Dictionary = helper._combat.contact_gotos[0]
	for frame in [48, 50, 56, 58, 59]:
		helper.play_source_frame(frame)
		var stale := helper._contact_clip_bounds(event)
		var current := helper.instance_global_bounds("atm1")
		print("FRAME_BOUNDARY ", JSON.stringify({"frame":frame,"placed_frame":event.placed_frame,"stale_bounds":[stale.position.x,stale.position.y,stale.size.x,stale.size.y],"current_bounds":[current.position.x,current.position.y,current.size.x,current.size.y]}))
		for distance in [50,150,250]:
			defender.source_x = 280.0 + distance
			defender.source_y = 0.0
			defender.set_facing(-1)
			defender.start_action("站立")
			var body := defender.instance_global_bounds("bdmn")
			print("DISTANCE ", JSON.stringify({"frame":frame,"distance":distance,"target_body":[body.position.x,body.position.y,body.size.x,body.size.y],"stale_contact":SourceHitTest.intersects(body,stale),"current_contact":SourceHitTest.intersects(body,current)}))
	helper.queue_free()
	owner.queue_free()
	defender.queue_free()
	await process_frame
	quit()
