class_name EnergyBar
extends Control

@export var mirrored: bool = false
var energy: float = 0.0:
	set(value):
		energy = clampf(value, 0.0, 300.0)
		queue_redraw()

const SEGMENT_COLORS := [Color("#168fd0"), Color("#19d892"), Color("#df2533")]


var helper_id: String = ""
var _helper_spec: Dictionary = {}
var _portrait_texture: Texture2D
var _border_texture: Texture2D
const PORTRAIT_DIRECTORY := "res://generated/main/helper_portraits"


func _ready() -> void:
	custom_minimum_size = Vector2(170.0, 38.0)
	queue_redraw()


func _draw() -> void:
	_draw_helper()
	# Source qitiao(): qi = round(ql)+1 drives the 0-100 bar frame, bs = floor(ql/100)+1
	# drives the stock counter. P1 is left, P2 is the mirrored right copy.
	var displayed := roundf(energy)
	var bar := Rect2(50.0, 15.0, 112.0, 12.0)
	var counter := Rect2(30.0, 6.0, 18.0, 29.0)
	if mirrored:
		bar.position.x = size.x - bar.end.x
		counter.position.x = size.x - counter.end.x
	draw_rect(bar.grow(2.0), Color("#d8f5ff"))
	draw_rect(bar.grow(1.0), Color("#15344e"))
	draw_rect(bar, Color("#020409"))
	var tier := mini(2, int(floorf(displayed / 100.0)))
	if displayed >= 100.0:
		draw_rect(bar, SEGMENT_COLORS[tier - 1])
	var progress := fmod(displayed, 100.0) / 100.0
	if displayed >= 300.0:
		progress = 1.0
	var fill := bar
	fill.size.x *= progress
	if mirrored:
		fill.position.x = bar.end.x - fill.size.x
	draw_rect(fill, SEGMENT_COLORS[tier])
	draw_rect(counter.grow(2.0), Color("#d8f5ff"))
	draw_rect(counter, SEGMENT_COLORS[tier].darkened(0.22))
	var font := ThemeDB.fallback_font
	var count := mini(3, int(floorf(displayed / 100.0)))
	var text_position := counter.position + Vector2(4.0, 22.0)
	draw_string(font, text_position, str(count), HORIZONTAL_ALIGNMENT_LEFT, -1.0, 20, Color("#07121c"))



func set_helper(value: String) -> void:
	helper_id = value
	_helper_spec = JSON.parse_string(FileAccess.get_file_as_string("%s/presentation.json" % PORTRAIT_DIRECTORY))
	var portrait: Dictionary = _helper_spec["portraits"].get(helper_id, {})
	_portrait_texture = null
	if not portrait.is_empty():
		_portrait_texture = load("%s/%s" % [PORTRAIT_DIRECTORY, portrait["texture"]])
	_border_texture = load("%s/%s" % [PORTRAIT_DIRECTORY, _helper_spec["border"]["texture"]])
	queue_redraw()


func _source_matrix(matrix: Dictionary) -> Transform2D:
	return Transform2D(
		Vector2(float(matrix.get("scaleX", 1.0)), float(matrix.get("rotateSkew0", 0.0))),
		Vector2(float(matrix.get("rotateSkew1", 0.0)), float(matrix.get("scaleY", 1.0))),
		Vector2(float(matrix.get("translateX", 0.0)), float(matrix.get("translateY", 0.0))))


func _draw_helper() -> void:
	if _portrait_texture == null:
		return
	# Original tx is 50.6 x 61 source pixels. Both HUD copies keep the face upright.
	var origin := Vector2(size.x - 30.3 if mirrored else 5.0, 5.0)
	var hud_transform := Transform2D(0.0, Vector2(0.5, 0.5), 0.0, origin)
	var border_matrix := _source_matrix(_helper_spec["border"]["matrix"])
	border_matrix.x /= 20.0
	border_matrix.y /= 20.0
	border_matrix.origin /= 20.0
	draw_set_transform_matrix(hud_transform * border_matrix)
	draw_texture(_border_texture, Vector2.ZERO)
	var portrait: Dictionary = _helper_spec["portraits"][helper_id]
	var placement := _source_matrix(_helper_spec["portrait_matrix"])
	placement.origin /= 20.0
	var bitmap := _source_matrix(portrait["matrix"])
	bitmap.x /= 20.0
	bitmap.y /= 20.0
	bitmap.origin /= 20.0
	var inverse := (placement * bitmap).affine_inverse()
	var points := PackedVector2Array()
	var uvs := PackedVector2Array()
	for point: Array in _helper_spec["mask"]:
		var vertex := Vector2(float(point[0]), float(point[1]))
		points.append(vertex)
		uvs.append((inverse * vertex) / _portrait_texture.get_size())
	draw_set_transform_matrix(hud_transform)
	draw_polygon(points, PackedColorArray([Color.WHITE]), uvs, _portrait_texture)
	var outline := PackedVector2Array()
	for point: Array in _helper_spec["outline"]:
		outline.append(Vector2(float(point[0]), float(point[1])))
	var rgba: Array = _helper_spec["outline_color"]
	draw_polyline(outline, Color(rgba[0], rgba[1], rgba[2], rgba[3]), float(_helper_spec["outline_width"]), true)
	draw_set_transform_matrix(Transform2D.IDENTITY)
