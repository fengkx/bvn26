class_name TimelinePreview
extends Node2D

@export var fighter_directory: String
@export var initial_action: String = "砍1"
@export var initial_frame: int = 1
@export var autoplay: bool = true
@export var show_collision_shapes: bool = true

var _timeline: Dictionary
var _fighter: Dictionary
var _definitions: Dictionary = {}
var _assets: Dictionary = {}
var _frames: Dictionary = {}
var _action_start: int
var _action_end: int
var _current_frame: int


func _ready() -> void:
	_load_data()
	if not _fighter.is_empty():
		play_action(initial_action)
	else:
		_current_frame = initial_frame
		_render_frame()


func _physics_process(_delta: float) -> void:
	if not autoplay or _fighter.is_empty():
		return
	if _current_frame >= _action_end:
		_current_frame = _action_start
	else:
		_current_frame += 1
	_render_frame()


func play_action(label: String) -> void:
	for group: Dictionary in _fighter["actions"].values():
		if group.has(label):
			_action_start = group[label]["start_frame"]
			_action_end = group[label]["end_frame"]
			_current_frame = _action_start
			_render_frame()
			return
	push_error("Unknown extracted action label: %s" % label)


func current_source_frame() -> int:
	return _current_frame


func action_range(label: String) -> Dictionary:
	for group: Dictionary in _fighter.get("actions", {}).values():
		if group.has(label):
			return group[label]
	return {}


func advance_source_frame(loop_action: bool = true) -> void:
	if _current_frame >= _action_end:
		if not loop_action:
			return
		_current_frame = _action_start
	else:
		_current_frame += 1
	_render_frame()


func instance_local_bounds(instance_name: String) -> Rect2:
	if not _frames.has(_current_frame):
		return Rect2()
	for placement: Dictionary in _frames[_current_frame]["display_list"]:
		if str(placement.get("name", "")) == instance_name:
			return _placement_bounds(placement)
	return Rect2()


func instance_global_bounds(instance_name: String) -> Rect2:
	var local_bounds := instance_local_bounds(instance_name)
	if local_bounds.has_area():
		return _transform_rect(global_transform, local_bounds)
	return Rect2()


func _load_data() -> void:
	_timeline = _read_json("%s/timeline.json" % fighter_directory)
	var fighter_path := "%s/fighter.json" % fighter_directory
	if FileAccess.file_exists(fighter_path):
		_fighter = _read_json(fighter_path)
	var asset_manifest: Dictionary = _read_json("%s/assets.json" % fighter_directory)
	for definition: Dictionary in _timeline["definitions"]:
		_definitions[int(definition["character_id"])] = definition
	for asset: Dictionary in asset_manifest["assets"]:
		_assets[int(asset["character_id"])] = asset["path"]
	for frame: Dictionary in _timeline["frames"]:
		_frames[int(frame["frame"])] = frame


func _read_json(path: String) -> Dictionary:
	var source := FileAccess.get_file_as_string(path)
	var value = JSON.parse_string(source)
	if not value is Dictionary:
		push_error("Cannot parse generated timeline data: %s" % path)
		return {}
	return value


func _render_frame() -> void:
	for child in get_children():
		child.queue_free()
	if not _frames.has(_current_frame):
		return
	var frame: Dictionary = _frames[_current_frame]
	for placement: Dictionary in frame["display_list"]:
		_render_placement(placement, Transform2D.IDENTITY, 1.0, 0, _current_frame)
	queue_redraw()


func _render_placement(
	placement: Dictionary,
	parent_transform: Transform2D,
	parent_alpha: float,
	parent_depth: int,
	timeline_frame: int
) -> void:
	var character_id := int(placement.get("character_id", -1))
	if not _definitions.has(character_id):
		return
	var definition: Dictionary = _definitions[character_id]
	var placement_transform := parent_transform * _matrix_transform(
		placement.get("matrix", {}), 1.0
	)
	var alpha := parent_alpha
	if placement.has("color_transform"):
		var color_transform: Dictionary = placement["color_transform"]
		alpha *= float(color_transform.get("alphaMultTerm", 256)) / 256.0
	var depth := parent_depth + int(placement["depth"])
	if definition["type"] == "DefineSpriteTag":
		var sprite_frames: Array = definition.get("display_list_frames", [])
		var local_frame := _nested_frame(placement, timeline_frame, sprite_frames.size())
		var children: Array = (
			sprite_frames[local_frame - 1]
			if not sprite_frames.is_empty()
			else definition.get("first_frame_display_list", [])
		)
		for child: Dictionary in children:
			_render_placement(child, placement_transform, alpha, depth, local_frame)
		return
	var fills: Array = definition.get("bitmap_fills", [])
	if not definition["type"].begins_with("DefineShape"):
		return
	var usable_fills: Array = fills.filter(
		func(fill: Dictionary) -> bool: return _assets.has(int(fill["bitmap_id"]))
	)
	for fill_index in usable_fills.size():
		var fill: Dictionary = usable_fills[fill_index]
		var bitmap_id := int(fill["bitmap_id"])
		var sprite := Sprite2D.new()
		sprite.centered = false
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		var source_texture: Texture2D = load("%s/%s" % [fighter_directory, _assets[bitmap_id]])
		sprite.z_index = depth + fill_index
		var bitmap_transform := _matrix_transform(fill.get("matrix", {}), 0.05)
		var draw_transform := bitmap_transform
		var texture_region := _shape_texture_region(definition, bitmap_transform, source_texture)
		if texture_region.has_area():
			var atlas := AtlasTexture.new()
			atlas.atlas = source_texture
			atlas.region = texture_region
			sprite.texture = atlas
			draw_transform.origin = bitmap_transform * texture_region.position
		else:
			sprite.texture = source_texture
		sprite.transform = placement_transform * draw_transform
		sprite.modulate.a = alpha
		add_child(sprite)


func _shape_texture_region(
	definition: Dictionary,
	bitmap_transform: Transform2D,
	texture: Texture2D
) -> Rect2:
	if not definition.has("shape_bounds_twips") or bitmap_transform.determinant() == 0.0:
		return Rect2()
	var bounds: Dictionary = definition["shape_bounds_twips"]
	var shape_rect := Rect2(
		Vector2(float(bounds["Xmin"]), float(bounds["Ymin"])) / 20.0,
		Vector2(
			float(bounds["Xmax"] - bounds["Xmin"]),
			float(bounds["Ymax"] - bounds["Ymin"])
		) / 20.0
	)
	var raw_region := _transform_rect(bitmap_transform.affine_inverse(), shape_rect)
	var start := Vector2(floorf(raw_region.position.x), floorf(raw_region.position.y))
	var finish := Vector2(ceilf(raw_region.end.x), ceilf(raw_region.end.y))
	start = start.max(Vector2.ZERO)
	finish = finish.min(Vector2(texture.get_width(), texture.get_height()))
	if finish.x <= start.x or finish.y <= start.y:
		return Rect2()
	return Rect2(start, finish - start)


func _matrix_transform(matrix: Dictionary, basis_scale: float) -> Transform2D:
	return Transform2D(
		Vector2(
			float(matrix.get("scaleX", 1.0)) * basis_scale,
			float(matrix.get("rotateSkew1", 0.0)) * basis_scale
		),
		Vector2(
			float(matrix.get("rotateSkew0", 0.0)) * basis_scale,
			float(matrix.get("scaleY", 1.0)) * basis_scale
		),
		Vector2(
			float(matrix.get("translateX", 0)) / 20.0,
			float(matrix.get("translateY", 0)) / 20.0
		)
	)


func _placement_bounds(placement: Dictionary, timeline_frame: int = _current_frame) -> Rect2:
	var definition: Dictionary = _definitions.get(int(placement.get("character_id", -1)), {})
	if definition.is_empty():
		return Rect2()
	var local_bounds := _definition_bounds(definition, placement, timeline_frame)
	if not local_bounds.has_area():
		return Rect2()
	return _transform_rect(
		_matrix_transform(placement.get("matrix", {}), 1.0),
		local_bounds
	)


func _definition_bounds(
	definition: Dictionary,
	placement: Dictionary,
	timeline_frame: int
) -> Rect2:
	if definition.has("shape_bounds_twips"):
		var bounds: Dictionary = definition["shape_bounds_twips"]
		return Rect2(
			Vector2(float(bounds["Xmin"]), float(bounds["Ymin"])) / 20.0,
			Vector2(
				float(bounds["Xmax"] - bounds["Xmin"]),
				float(bounds["Ymax"] - bounds["Ymin"])
			) / 20.0
		)
	if definition["type"] != "DefineSpriteTag":
		return Rect2()
	var sprite_frames: Array = definition.get("display_list_frames", [])
	var local_frame := _nested_frame(placement, timeline_frame, sprite_frames.size())
	var children: Array = (
		sprite_frames[local_frame - 1]
		if not sprite_frames.is_empty()
		else definition.get("first_frame_display_list", [])
	)
	var result := Rect2()
	for child: Dictionary in children:
		var child_bounds := _placement_bounds(child, local_frame)
		if not child_bounds.has_area():
			continue
		result = child_bounds if not result.has_area() else result.merge(child_bounds)
	return result


func _nested_frame(placement: Dictionary, timeline_frame: int, frame_count: int) -> int:
	if frame_count <= 1:
		return 1
	var placed_frame := int(placement.get("placed_frame", timeline_frame))
	return posmod(maxi(0, timeline_frame - placed_frame), frame_count) + 1


func _transform_rect(transform_2d: Transform2D, rectangle: Rect2) -> Rect2:
	var corners := [
		transform_2d * rectangle.position,
		transform_2d * Vector2(rectangle.end.x, rectangle.position.y),
		transform_2d * rectangle.end,
		transform_2d * Vector2(rectangle.position.x, rectangle.end.y),
	]
	var minimum: Vector2 = corners[0]
	var maximum: Vector2 = corners[0]
	for corner: Vector2 in corners.slice(1):
		minimum = minimum.min(corner)
		maximum = maximum.max(corner)
	return Rect2(minimum, maximum - minimum)


func _draw() -> void:
	if not show_collision_shapes or not _frames.has(_current_frame):
		return
	for placement: Dictionary in _frames[_current_frame]["display_list"]:
		var instance_name := str(placement.get("name", ""))
		if instance_name == "bdmn" or instance_name.ends_with("atm"):
			_draw_collision_shape(placement, instance_name.ends_with("atm"))


func _draw_collision_shape(placement: Dictionary, is_attack: bool) -> void:
	var definition: Dictionary = _definitions.get(int(placement.get("character_id", -1)), {})
	var references: Array = definition.get("referenced_character_ids", [])
	if references.size() != 1:
		return
	var shape: Dictionary = _definitions.get(int(references[0]), {})
	if not shape.has("shape_bounds_twips"):
		return
	var bounds: Dictionary = shape["shape_bounds_twips"]
	var matrix: Dictionary = placement.get("matrix", {})
	var position_twips := Vector2(float(bounds["Xmin"]), float(bounds["Ymin"]))
	var size_twips := Vector2(
		float(bounds["Xmax"] - bounds["Xmin"]),
		float(bounds["Ymax"] - bounds["Ymin"])
	)
	var rectangle := Rect2(position_twips / 20.0, size_twips / 20.0)
	var transform_2d := Transform2D(
		Vector2(float(matrix.get("scaleX", 1.0)), float(matrix.get("rotateSkew1", 0.0))),
		Vector2(float(matrix.get("rotateSkew0", 0.0)), float(matrix.get("scaleY", 1.0))),
		Vector2(
			float(matrix.get("translateX", 0)) / 20.0,
			float(matrix.get("translateY", 0)) / 20.0
		)
	)
	var color := Color(1.0, 0.2, 0.16, 0.28) if is_attack else Color(0.2, 0.65, 1.0, 0.18)
	draw_set_transform_matrix(transform_2d)
	draw_rect(rectangle, color, true)
	draw_rect(rectangle, color.lightened(0.35), false, 1.0)
	draw_set_transform_matrix(Transform2D.IDENTITY)
