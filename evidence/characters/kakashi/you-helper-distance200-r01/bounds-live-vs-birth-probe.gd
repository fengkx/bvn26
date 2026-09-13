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
	root.add_child(owner); root.add_child(defender); root.add_child(helper)
	await process_frame
	owner.opponent = defender; defender.opponent = owner
	for facing in [1, -1]:
		var helper_x = 280.0 if facing == 1 else 500.0
		helper.position = Vector2(helper_x, -25.0); helper.set_facing(facing)
		for frame in [48, 50, 56, 58, 59]:
			helper.play_source_frame(frame)
			var birth: Dictionary
			var live: Dictionary
			for p: Dictionary in helper._frames[48]["display_list"]:
				if int(p.get("depth", -1)) == 3: birth = p
			for p: Dictionary in helper._frames[frame]["display_list"]:
				if int(p.get("depth", -1)) == 3: live = p
			var birth_box := helper.source_placement_global_bounds(birth, 48)
			var live_box := helper.source_placement_global_bounds(live, frame)
			for distance in [50, 150, 200, 250]:
				defender.source_x = helper_x + facing * distance
				defender.source_y = 0.0
				defender.sync_body_collision_position()
				defender.set_facing(-facing)
				defender.start_action("站立")
				var body := defender.instance_global_bounds("bdmn")
				print("LIVE_BOUNDS ", JSON.stringify({"facing":facing,"frame":frame,"distance":distance,"birth":[birth_box.position.x,birth_box.position.y,birth_box.size.x,birth_box.size.y],"live":[live_box.position.x,live_box.position.y,live_box.size.x,live_box.size.y],"body":[body.position.x,body.position.y,body.size.x,body.size.y],"birth_intersects":SourceHitTest.intersects(body,birth_box),"live_intersects":SourceHitTest.intersects(body,live_box)}))
	quit()
