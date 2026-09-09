extends SceneTree


func _initialize() -> void:
	var receiver := Rect2(0, 0, 10, 10)
	# Native Flash dash_edge cases: edge/corner contact is true; one twip
	# of separation is false. No epsilon or expanded geometry is involved.
	for offset in [Vector2(10, 0), Vector2(10, 10), Vector2(9.95, 0), Vector2(-10, 0), Vector2(-10, -10)]:
		assert(SourceHitTest.intersects(receiver, Rect2(offset, Vector2(10, 10))))
	for offset in [Vector2(10.05, 0), Vector2(0, 10.05)]:
		assert(not SourceHitTest.intersects(receiver, Rect2(offset, Vector2(10, 10))))
	assert(not SourceHitTest.intersects(receiver, Rect2()))
	assert(not SourceHitTest.intersects(Rect2(), receiver))
	print("SOURCE_HIT_TEST_SMOKE_OK")
	quit()
