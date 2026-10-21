extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	# These stop frames are independently sampled from the original symbols.
	var helper := HelperRuntime.new()
	helper.helper_directory = "res://generated/helpers/woailuo"
	helper.play_timeline_sounds = false
	root.add_child(helper)
	helper.attacking = true
	helper.timeline_playing = false
	helper.play_source_frame(44)
	assert(helper.instance_clip_frame("atm1") == 1)
	for tick in 40:
		helper.advance_timeline()
		assert(helper.current_source_frame() == 44)
		assert(helper.instance_clip_frame("atm1") == mini(tick + 2, 33))
	helper.play_source_frame(45)
	helper.advance_timeline()
	assert(helper.instance_clip_frame("atm1") == 33)
	helper.free()

	var caster := FighterRuntime.new()
	var stage := StageHitRuntime.new()
	stage.configure("res://generated/effects/XG_baoqi", caster, {})
	stage.play_timeline_sounds = false
	root.add_child(stage)
	for tick in 18:
		stage.advance_timeline()
		assert(stage.unnamed_sprite_local_frame(510) == mini(tick + 2, 16))
	stage.free()
	caster.free()

	var effect := HitEffectRuntime.new()
	effect.auto_advance = false
	effect.defer_initial_frame = true
	root.add_child(effect)
	effect.configure("XG_baoqi", Vector2.ZERO, 1)
	# Exercise the production visual host independently of sound/root services.
	effect._events = []
	effect._sound_events = {}
	for tick in 18:
		effect.advance_effect()
		assert(effect._preview.unnamed_sprite_local_frame(510) == mini(tick + 2, 16))
	effect.free()
	print("RETAINED_EFFECT_CLOCKS_OK helper_pause helper_goto stage_hit hit_effect")
	quit()
