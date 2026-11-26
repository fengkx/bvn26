extends SceneTree

const BlendGroup := preload("res://blend_group.gd")


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var destination := SubViewport.new()
	destination.size = Vector2i(1200, 800)
	destination.size_2d_override = Vector2i(600, 400)
	destination.size_2d_override_stretch = true
	root.add_child(destination)
	var shape := Polygon2D.new()
	shape.polygon = PackedVector2Array([
		Vector2(-200, -200), Vector2(1000, -200), Vector2(1000, 700), Vector2(-200, 700),
	])
	var group := BlendGroup.new()
	group.clip_offscreen = true
	var composite := group.setup([shape], 1.0)
	group.add_child(composite)
	destination.add_child(group)

	assert(group.cache_allocation() == Vector2i(1200, 900))
	destination.set_meta("clip_offscreen_caches", true)
	group._update_buffer()
	assert(group.uncropped_size == Vector2i(1200, 900))
	assert(group.cache_allocation() == Vector2i(602, 402))
	assert(composite.global_position == Vector2(-1, -1))

	group.position.x = 1000.0
	group.force_update_transform()
	assert(group.cache_allocation() == Vector2i(2, 2))
	assert(not composite.visible)
	group.position.x = -300.0
	group.force_update_transform()
	assert(group.cache_allocation() == Vector2i(602, 402))
	assert(composite.visible and composite.global_position == Vector2(-1, -1))
	destination.free()
	print("OFFSCREEN_CACHE_BOUNDS_OK")
	quit()
