extends Node2D

var clip_offscreen := false
var uncropped_size := Vector2i.ZERO

# A non-normal Flash blend belongs to the composed display object, including
# its children. Keep the offscreen buffer aligned to destination pixels.
func setup(items: Array, opacity: float) -> Sprite2D:
	var viewport := SubViewport.new()
	viewport.name = "Contents"
	viewport.transparent_bg = true
	viewport.world_2d = World2D.new()
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(viewport)
	for item: CanvasItem in items:
		item.set_meta("blend_source_transform", item.transform)
		item.z_index = 0
		viewport.add_child(item)
	var composite := Sprite2D.new()
	composite.name = "Composite"
	composite.centered = false
	composite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	composite.modulate.a = opacity
	return composite


func _ready() -> void:
	# Rebind after duplicate() as well: a visual snapshot owns its viewport.
	$Composite.texture = $Contents.get_texture()
	set_notify_transform(true)
	_update_buffer()


func _notification(what: int) -> void:
	if what == NOTIFICATION_TRANSFORM_CHANGED and is_inside_tree() and has_node("Composite"):
		_update_buffer()


func source_bounds() -> Rect2:
	var result := Rect2()
	var found := false
	for item in $Contents.get_children():
		var bounds := Rect2()
		if item is Sprite2D:
			bounds = item.get_rect()
		elif item is Polygon2D:
			if not item.polygon.is_empty():
				bounds = Rect2(item.polygon[0], Vector2.ZERO)
				for point: Vector2 in item.polygon:
					bounds = bounds.expand(point)
		elif item.has_method("source_bounds"):
			bounds = item.source_bounds()
		if not bounds.has_area():
			continue
		var transform: Transform2D = item.get_meta("blend_source_transform")
		bounds = transform * bounds
		result = result.merge(bounds) if found else bounds
		found = true
	return result


func buffer_padding() -> Vector2:
	return Vector2.ZERO


func _update_buffer() -> void:
	var transform := global_transform
	if transform.determinant() == 0.0:
		return
	var bounds := transform * source_bounds()
	var padding := buffer_padding()
	bounds = bounds.grow_individual(padding.x, padding.y, padding.x, padding.y)
	uncropped_size = Vector2i((bounds.end.ceil() - bounds.position.floor()).max(Vector2.ONE))
	var viewport := get_viewport()
	if clip_offscreen and viewport is SubViewport and viewport.has_meta("clip_offscreen_caches"):
		# The composite samples this texture with nearest filtering. Keep its
		# original integer grid and one pixel of margin at the destination edge.
		var target := Rect2(Vector2.ZERO, Vector2(viewport.size_2d_override))
		var canvas := get_canvas_transform()
		if target.has_area() and canvas.determinant() != 0.0:
			var visible_bounds := (canvas.affine_inverse() * target).grow(1.0)
			bounds = bounds.intersection(visible_bounds)
			$Composite.visible = bounds.has_area()
			if not bounds.has_area():
				$Contents.size = Vector2i(2, 2)
				return
	var origin := bounds.position.floor()
	var extent := (bounds.end.ceil() - origin).max(Vector2.ONE)
	$Contents.size = Vector2i(extent)
	var shift := Transform2D(0.0, -origin)
	for item in $Contents.get_children():
		item.transform = shift * transform * Transform2D(item.get_meta("blend_source_transform"))
	$Composite.transform = transform.affine_inverse() * Transform2D(0.0, origin)


func cache_allocation() -> Vector2i:
	return $Contents.size
