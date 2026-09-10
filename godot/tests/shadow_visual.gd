extends Node

var game
var shadow: ShadowSnapshot

func _ready() -> void:
	_run.call_deferred()

func _run() -> void:
	game = load("res://main.tscn").instantiate()
	add_child(game)
	game.set_physics_process(false)
	game._load_selected_stage("现世")
	game._enter_current_fight(3)
	for tick in 700:
		game._advance_fight()
		if not game.battle_intro.active:
			break
	var actor: FighterRuntime = game.naruto
	actor.goto_ai_label("走", false)
	actor.source_x = 360
	actor.source_y = -25
	actor.set_facing(1)
	game.ichigo.source_x = 580
	game.ichigo.source_y = -25
	game.ichigo.goto_ai_label("站立", false)
	game._fighter_visual_service(actor, "showdow", [{"R":20, "G":-100, "B":255}])
	for child in game.game_world.get_children():
		if child is ShadowSnapshot:
			shadow = child
	assert(shadow != null)
	actor.source_x += 55
	game.game_world.snap(actor, game.ichigo)
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var before := shadow.capture_viewport.get_texture().get_image()
	assert(not before.is_invisible(), "Snapshot bitmap must contain the fighter")
	actor.goto_ai_label("砍1", false)
	actor.set_facing(-1)
	actor.source_x += 25
	shadow.fade()
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var after := shadow.capture_viewport.get_texture().get_image()
	assert(before.get_data() == after.get_data(), "Snapshot pixels must not animate with the source actor")
	print("SHADOW_VISUAL_OK bitmap=", shadow.bitmap_size, " frozen_pixels=true")
	if OS.has_feature("web"):
		JavaScriptBridge.eval("window.shadowVisualResult = 'passed';")
	else:
		get_viewport().get_texture().get_image().save_png("/tmp/bvn-shadow-scene.png")
		before.save_png("/tmp/bvn-shadow-bitmap.png")
		game._goto_menu()
		game.queue_free()
		await get_tree().process_frame
		get_tree().quit()
