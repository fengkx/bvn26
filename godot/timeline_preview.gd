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
var _instance_local_offsets: Dictionary = {}
var _instance_local_frames: Dictionary = {}


func _ready() -> void:
	_load_data()
	if _frames.is_empty():
		return
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
	_instance_local_offsets.clear()
	_instance_local_frames.clear()
	for group: Dictionary in _fighter["actions"].values():
		if group.has(label):
			_action_start = group[label]["start_frame"]
			_action_end = group[label]["end_frame"]
			_current_frame = _action_start
			_render_frame()
			return
	push_error("Unknown extracted action label: %s" % label)


func play_source_frame(frame: int) -> void:
	_current_frame = frame
	_render_frame()


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
			return _rooted_placement_bounds(placement)
	return Rect2()


func instance_global_bounds(instance_name: String) -> Rect2:
	var local_bounds := instance_local_bounds(instance_name)
	if local_bounds.has_area():
		return _transform_rect(global_transform, local_bounds)
	return Rect2()


func named_instances_global_bounds(prefix: String) -> Array[Rect2]:
	var result: Array[Rect2] = []
	for local_bounds in named_instances_local_bounds(prefix):
		result.append(_transform_rect(global_transform, local_bounds))
	return result


func named_instances_local_bounds(prefix: String) -> Array[Rect2]:
	var result: Array[Rect2] = []
	if not _frames.has(_current_frame):
		return result
	for placement: Dictionary in _frames[_current_frame]["display_list"]:
		if not str(placement.get("name", "")).begins_with(prefix):
			continue
		var local_bounds := _rooted_placement_bounds(placement)
		if local_bounds.has_area():
			result.append(local_bounds)
	return result


func named_instance_ledges(prefix: String) -> Array[Rect2]:
	# Source isHitBan() in fighter DefineSprite_*/frame_1/DoAction.as:
	# stand on ban._y (clip registration), x in [ban._x, ban._x + ban._width].
	# Shape AABB top is not the walkable plane when Ymin != 0.
	var result: Array[Rect2] = []
	if not _frames.has(_current_frame):
		return result
	for placement: Dictionary in _frames[_current_frame]["display_list"]:
		var instance_name := str(placement.get("name", ""))
		if not instance_name.begins_with(prefix):
			continue
		var local_bounds := _placement_bounds(placement)
		if not local_bounds.has_area():
			continue
		var matrix: Dictionary = placement.get("matrix", {})
		result.append(
			Rect2(
				float(matrix.get("translateX", 0.0)) / 20.0,
				float(matrix.get("translateY", 0.0)) / 20.0,
				local_bounds.size.x,
				10.0
			)
		)
	return result


func wrapper_translation() -> Vector2:
	var wrapper = _timeline.get("wrapper", {})
	if typeof(wrapper) != TYPE_DICTIONARY or wrapper.is_empty():
		return Vector2.ZERO
	var matrix: Dictionary = wrapper.get("matrix", {})
	return Vector2(
		float(matrix.get("translateX", 0.0)) / 20.0,
		float(matrix.get("translateY", 0.0)) / 20.0
	)


func named_instance_origin(instance_name: String) -> Vector2:
	if not _frames.has(_current_frame):
		return Vector2.INF
	for placement: Dictionary in _frames[_current_frame]["display_list"]:
		if str(placement.get("name", "")) != instance_name:
			continue
		var matrix: Dictionary = placement.get("matrix", {})
		return Vector2(
			float(matrix.get("translateX", 0.0)) / 20.0,
			float(matrix.get("translateY", 0.0)) / 20.0
		)
	return Vector2.INF


func instance_local_offset(instance_name: String) -> Vector2:
	return _instance_local_offsets.get(instance_name, Vector2.ZERO)


func set_instance_local_offset(instance_name: String, offset: Vector2) -> void:
	_instance_local_offsets[instance_name] = offset


func set_instance_clip_frame(
	instance_name: String,
	local_frame: int,
	playing: bool = true,
	age: int = -1
) -> void:
	var previous: Dictionary = _instance_local_frames.get(instance_name, {})
	_instance_local_frames[instance_name] = {
		"anchor_timeline": _current_frame,
		"local_start": local_frame,
		"playing": playing,
		"age": int(previous.get("age", 0)) if age < 0 else age,
	}


func instance_clip_playing(instance_name: String) -> bool:
	return bool(_instance_local_frames.get(instance_name, {}).get("playing", false))


func instance_clip_age(instance_name: String) -> int:
	return int(_instance_local_frames.get(instance_name, {}).get("age", 0))


func instance_clip_frame(instance_name: String) -> int:
	if not _frames.has(_current_frame):
		return 0
	for placement: Dictionary in _frames[_current_frame]["display_list"]:
		if str(placement.get("name", "")) != instance_name:
			continue
		var definition: Dictionary = _definitions.get(int(placement.get("character_id", -1)), {})
		var sprite_frames: Array = definition.get("display_list_frames", [])
		return _nested_frame(placement, _current_frame, sprite_frames.size())
	return 0


func unnamed_sprite_local_frame(character_id: int) -> int:
	if not _frames.has(_current_frame):
		return 0
	for placement: Dictionary in _frames[_current_frame]["display_list"]:
		if int(placement.get("character_id", -1)) != character_id:
			continue
		if str(placement.get("name", "")) != "":
			continue
		var definition: Dictionary = _definitions.get(character_id, {})
		var sprite_frames: Array = definition.get("display_list_frames", [])
		return _nested_frame(placement, _current_frame, sprite_frames.size())
	return 0


func refresh_display() -> void:
	_render_frame()


func current_named_instances() -> PackedStringArray:
	var result: PackedStringArray = []
	if not _frames.has(_current_frame):
		return result
	for placement: Dictionary in _frames[_current_frame]["display_list"]:
		var instance_name := str(placement.get("name", ""))
		if instance_name != "":
			result.append(instance_name)
	return result


func _load_data() -> void:
	if fighter_directory == "":
		return
	var timeline_path := "%s/timeline.json" % fighter_directory
	var timeline_source := FileAccess.get_file_as_string(timeline_path)
	if timeline_source == "":
		return
	_timeline = _read_json(timeline_path)
	if _timeline.is_empty() or not _timeline.has("frames"):
		return
	var fighter_path := "%s/fighter.json" % fighter_directory
	if FileAccess.file_exists(fighter_path):
		_fighter = _read_json(fighter_path)
	var asset_manifest: Dictionary = {}
	var assets_path := "%s/assets.json" % fighter_directory
	var assets_source := FileAccess.get_file_as_string(assets_path)
	if assets_source != "":
		asset_manifest = _read_json(assets_path)
	for definition: Dictionary in _timeline.get("definitions", []):
		_definitions[int(definition["character_id"])] = definition
	for asset: Dictionary in asset_manifest.get("assets", []):
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
	var wrapper := _wrapper_transform()
	for placement: Dictionary in frame["display_list"]:
		_render_placement(placement, wrapper, 1.0, 0, _current_frame, 0)
	queue_redraw()


func _render_placement(
	placement: Dictionary,
	parent_transform: Transform2D,
	parent_alpha: float,
	parent_depth: int,
	timeline_frame: int,
	clip_age: int = 0
) -> void:
	var character_id := int(placement.get("character_id", -1))
	if not _definitions.has(character_id):
		return
	var definition: Dictionary = _definitions[character_id]
	var placement_transform := parent_transform * _placement_transform(placement)
	var alpha := parent_alpha
	if placement.has("color_transform"):
		var color_transform: Dictionary = placement["color_transform"]
		alpha *= float(color_transform.get("alphaMultTerm", 256)) / 256.0
	var depth := parent_depth + int(placement["depth"])
	if definition["type"] == "DefineSpriteTag":
		var sprite_frames: Array = definition.get("display_list_frames", [])
		var local_frame := _nested_frame(
			placement, timeline_frame, sprite_frames.size(), clip_age
		)
		var child_age := clip_age
		var instance_name := str(placement.get("name", ""))
		if instance_name != "" and _instance_local_frames.has(instance_name):
			child_age = int(_instance_local_frames[instance_name].get("age", 0))
		var children: Array = (
			sprite_frames[local_frame - 1]
			if not sprite_frames.is_empty()
			else definition.get("first_frame_display_list", [])
		)
		for child: Dictionary in children:
			_render_placement(
				child, placement_transform, alpha, depth, local_frame, child_age
			)
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


func _placement_transform(placement: Dictionary) -> Transform2D:
	var transform_2d := _matrix_transform(placement.get("matrix", {}), 1.0)
	transform_2d.origin += instance_local_offset(str(placement.get("name", "")))
	return transform_2d


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


func _wrapper_transform() -> Transform2D:
	# Fighter SWF root places the inner timeline as `mc`. Player `_x/_y`
	# stays on the wrapper; this matrix is the missing visual/hitbox offset.
	var wrapper = _timeline.get("wrapper", {})
	if typeof(wrapper) != TYPE_DICTIONARY or wrapper.is_empty():
		return Transform2D.IDENTITY
	return _matrix_transform(wrapper.get("matrix", {}), 1.0)


func _rooted_placement_bounds(placement: Dictionary, timeline_frame: int = _current_frame) -> Rect2:
	var local_bounds := _placement_bounds(placement, timeline_frame)
	if not local_bounds.has_area():
		return local_bounds
	return _transform_rect(_wrapper_transform(), local_bounds)


func _placement_bounds(placement: Dictionary, timeline_frame: int = _current_frame) -> Rect2:
	var definition: Dictionary = _definitions.get(int(placement.get("character_id", -1)), {})
	if definition.is_empty():
		return Rect2()
	var local_bounds := _definition_bounds(definition, placement, timeline_frame)
	if not local_bounds.has_area():
		return Rect2()
	return _transform_rect(_placement_transform(placement), local_bounds)


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


func _nested_frame(
	placement: Dictionary,
	timeline_frame: int,
	frame_count: int,
	clip_age: int = 0
) -> int:
	var instance_name := str(placement.get("name", ""))
	if instance_name != "" and _instance_local_frames.has(instance_name):
		return maxi(1, int(_instance_local_frames[instance_name]["local_start"]))
	if frame_count <= 1:
		return 1
	# Unnamed clips inside a projectile playhead keep that clip's age so they
	# do not follow the fighter timeline. Root unnamed clips (walk body, etc.)
	# have clip_age 0 and must sync from placed_frame, otherwise they stay
	# on local frame 1 and the character only translates.
	if instance_name == "" and clip_age > 0:
		return posmod(clip_age, frame_count) + 1
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
	var rectangle := Rect2(
		Vector2(float(bounds["Xmin"]), float(bounds["Ymin"])) / 20.0,
		Vector2(
			float(bounds["Xmax"] - bounds["Xmin"]),
			float(bounds["Ymax"] - bounds["Ymin"])
		) / 20.0
	)
	var transform_2d := _wrapper_transform() * _placement_transform(placement)
	var color := Color(1.0, 0.2, 0.16, 0.28) if is_attack else Color(0.2, 0.65, 1.0, 0.18)
	draw_set_transform_matrix(transform_2d)
	draw_rect(rectangle, color, true)
	draw_rect(rectangle, color.lightened(0.35), false, 1.0)
	draw_set_transform_matrix(Transform2D.IDENTITY)
