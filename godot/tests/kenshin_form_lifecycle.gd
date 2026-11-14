extends SceneTree
const Fixture = preload("res://tests/rollback_fixture.gd")

func _initialize() -> void:
	_run.call_deferred()

func _replace(game: Node, source_frame: int, target_sprite: int, target_frame: int, tick: int) -> void:
	var fighter: FighterRuntime = game.naruto
	var driver: AiCpuDriver = game.player_body_driver._driver
	fighter.source_goto_frame(source_frame, true)
	driver.run_target_frames()
	assert(not fighter.source_body_available)
	driver.prepare_display_tick(tick)
	driver.advance_timeline()
	driver.run_target_frames()
	assert(fighter.source_body_available)
	assert(int(fighter._timeline.sprite_id) == target_sprite)
	assert(fighter.current_source_frame() == target_frame)

func _run() -> void:
	var fixture := Fixture.create(self, ["剑心", "一护"], ["我爱罗", "魂"])
	var game: Node = fixture.game
	game.source_root_intervals.recorded = true
	for edge in [{"source": 1148, "sprite": 1473, "frame": 1375, "tick": 1},
			{"source": 1503, "sprite": 2506, "frame": 972, "tick": 2}]:
		var fighter: FighterRuntime = game.naruto
		fighter.health = 671
		fighter.energy = 234
		fighter.ai_source_state.values.wudi = false
		fighter.ai_source_state.values.__sentinel = 73
		var before: Dictionary = fixture.battle.save_state()
		assert(not before.has("error"), str(before))
		_replace(game, edge.source, edge.sprite, edge.frame, edge.tick)
		assert(game.naruto.health == 671 and game.naruto.energy == 234)
		assert(game.naruto.ai_source_state.read_field("__sentinel") == null)
		var after: Dictionary = fixture.battle.save_state()
		assert(not after.has("error"), str(after))
		assert(fixture.battle.load_state(before).is_empty())
		assert(game.naruto.ai_source_state.read_field("__sentinel") == 73)
		_replace(game, edge.source, edge.sprite, edge.frame, edge.tick)
		assert(fixture.battle.load_state(after).is_empty())
		var timers: SourceRootIntervals = game.source_root_intervals
		assert(int(timers.handles.feiint) == edge.tick)
		if edge.tick == 2: assert(not timers.fire_recorded(1))
		game.naruto.root_zhanting = true
		assert(timers.fire_recorded(edge.tick))
		assert(game.naruto.health == 671)
		game.naruto.root_zhanting = false
		assert(timers.fire_recorded(edge.tick))
		assert(game.naruto.health == 661)
		game.naruto.health = 201
		assert(timers.fire_recorded(edge.tick))
		assert(game.naruto.health == 191)
		assert(timers.fire_recorded(edge.tick))
		assert(game.naruto.health == 191)
		print("KENSHIN_FORM_EDGE_OK ", edge.sprite)
	assert(game.naruto._wrapper_visual_clips.has(45))
	var visual_before: Dictionary = fixture.battle.save_state()
	var frame: int = game.naruto._wrapper_visual_clips[45].frame
	game.naruto.advance_retained_visual_clips()
	assert(game.naruto._wrapper_visual_clips[45].frame != frame)
	assert(fixture.battle.load_state(visual_before).is_empty())
	assert(game.naruto._wrapper_visual_clips[45].frame == frame)
	Fixture.dispose(game, fixture.battle)
	await process_frame
	print("KENSHIN_FORM_LIFECYCLE_OK 2 edges; transfer, local reset, timer replacement, pause, threshold, visual clock and rollback")
	quit()
