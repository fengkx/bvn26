class_name EnergyBar
extends Control

@export var mirrored: bool = false
var _pending_energy := 0.0
var _display_energy := 0.0
var energy: float:
	get:
		return _pending_energy
	set(value):
		_pending_energy = clampf(value, 0.0, 300.0)
		_display_energy = _pending_energy
		queue_redraw()

var helper_id: String = ""
var _helper_spec: Dictionary = {}
var _portrait_texture: Texture2D
var _border_texture: Texture2D
const PORTRAIT_DIRECTORY := "res://generated/main/helper_portraits"
const SOURCE_DIRECTORY := "res://generated/main/energy"
var _source_spec: Dictionary = {}
var _source_background: Texture2D
var _source_qt: Array[Texture2D] = []
var _source_qt_nested: Array[Texture2D] = []
var _source_bss: Array[Texture2D] = []
var _source_qt_base: Texture2D
var _source_qt_overlay: Texture2D
var _qt_child_frame := 1
var _last_qt_frame := 0
var _last_display_tick := -1


func _ready() -> void:
	_source_spec = JSON.parse_string(FileAccess.get_file_as_string(SOURCE_DIRECTORY + "/presentation.json"))
	var layout: Dictionary = _source_spec["layout"]
	var bounds: Dictionary = layout["wrapper_composite_bounds"]
	var outer_scale := float(layout["active_outer_instances"]["p1"]["scaleX"])
	custom_minimum_size = Vector2(
		(float(bounds["maxX"]) - float(bounds["minX"])) * outer_scale,
		(float(bounds["maxY"]) - float(bounds["minY"])) * outer_scale)
	_source_background = load(SOURCE_DIRECTORY + "/background.png")
	for frame in range(1, 302):
		_source_qt.append(load(SOURCE_DIRECTORY + "/qt/%d.png" % frame))
	for frame in range(1, 11):
		_source_qt_nested.append(load(SOURCE_DIRECTORY + "/qt-nested/%d.png" % frame))
	_source_qt_base = load(SOURCE_DIRECTORY + "/qt-layers/base-1759.png")
	_source_qt_overlay = load(SOURCE_DIRECTORY + "/qt-layers/overlay-1756.png")
	for frame in range(1, 5):
		# Source load mapping is P1->bss1781 and P2->bss1773; the latter is
		# selected by the mirrored (right-side) HUD instance.
		_source_bss.append(load(SOURCE_DIRECTORY + ("/bss-p1/%d.png" if mirrored else "/bss-p2/%d.png") % frame))
	queue_redraw()


func advance_display_tick(display_tick: int) -> void:
	# DefineSprite_1763 advances once per display tick while qt is on frame
	# 301. It must not advance from repeated ql assignments in one tick.
	if display_tick == _last_display_tick:
		return
	_last_display_tick = display_tick
	var qt_frame := clampi(roundi(_display_energy) + 1, 1, int(_source_spec.get("qt_frames", 301)))
	if _source_qt_nested.is_empty():
		return
	if qt_frame == 301:
		if _last_qt_frame != 301:
			_qt_child_frame = 1
		else:
			_qt_child_frame = (_qt_child_frame % _source_qt_nested.size()) + 1
	else:
		_qt_child_frame = 1
	_last_qt_frame = qt_frame
	queue_redraw()


func _draw() -> void:
	# The source wrapper child union is compiled in presentation.json. Its
	# qt/bss children are authored timeline clips, so draw their exported
	# frames instead of approximating the meter with rectangles.
	draw_set_transform_matrix(_source_outer_transform())
	var qi := clampi(roundi(_display_energy) + 1, 1, int(_source_spec.get("qt_frames", 301)))
	var bs := clampi(floori(_display_energy / 100.0) + 1, 1, int(_source_spec.get("bss_frames", 4)))
	var wrapper_name := "p2" if mirrored else "p1"
	var placements: Dictionary = _source_spec["wrappers"][wrapper_name]["placements"]
	var background_position := Vector2(float(placements["background"]["x"]), float(placements["background"]["y"]))
	var qt_position := Vector2(float(placements["qt"]["x"]), float(placements["qt"]["y"]))
	var bss_position := Vector2(float(placements["bss"]["x"]), float(placements["bss"]["y"]))
	if _source_background != null:
		draw_texture(_source_background, background_position)
	if qi == 301:
		# Keep qt frame 301's authored display list: depth 1 base, depth 2
		# nested meter child, then depth 4 overlay. Do not replace or crop qt.
		var layer_spec: Dictionary = _source_spec.get("qt_layers", {})
		var base_matrix: Dictionary = layer_spec.get("depth1_base", {}).get("matrix", {})
		var nested_matrix: Dictionary = layer_spec.get("depth2_nested", {}).get("matrix", {})
		var overlay_matrix: Dictionary = layer_spec.get("depth4_overlay", {}).get("matrix", {})
		var base_bounds: Array = layer_spec.get("depth1_base", {}).get("bounds_twips", [6, 0, 2806, 360])
		var base_offset := Vector2(float(base_matrix.get("translateX", 0.0)) + float(base_bounds[0]), float(base_matrix.get("translateY", 0.0)) + float(base_bounds[1])) / 20.0
		var nested_offset := Vector2(float(nested_matrix.get("translateX", 0.0)), float(nested_matrix.get("translateY", 0.0))) / 20.0
		var overlay_offset := Vector2(float(overlay_matrix.get("translateX", 0.0)), float(overlay_matrix.get("translateY", 0.0))) / 20.0
		if _source_qt_base != null:
			draw_texture(_source_qt_base, qt_position + base_offset)
		if _source_qt_nested[_qt_child_frame - 1] != null:
			draw_texture(_source_qt_nested[_qt_child_frame - 1], qt_position + nested_offset)
		if _source_qt_overlay != null:
			draw_texture(_source_qt_overlay, qt_position + overlay_offset)
	elif _source_qt[qi - 1] != null:
		draw_texture(_source_qt[qi - 1], qt_position)
	if bs <= _source_bss.size() and _source_bss[bs - 1] != null:
		var bss_symbol := "1773" if mirrored else "1781"
		var bss_bounds: Dictionary = _source_spec.get("bss_source_bounds_twips", {}).get(bss_symbol, {})
		var bss_origin := Vector2(float(bss_bounds.get("xmin", 0.0)), float(bss_bounds.get("ymin", 0.0))) / 20.0
		draw_texture(_source_bss[bs - 1], bss_position + bss_origin)
	draw_set_transform_matrix(Transform2D.IDENTITY)
	_draw_helper()



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
	# tx is placed at (-80,-80) twips inside both source wrappers. The source
	# wrapper matrix supplies the authored scale and P2 mirroring.
	var tx_transform := Transform2D.IDENTITY
	tx_transform.origin = Vector2(-80.0, -80.0) / 20.0
	var hud_transform := _source_outer_transform() * tx_transform
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


func _source_outer_transform() -> Transform2D:
	var layout: Dictionary = _source_spec["layout"]
	var instances: Dictionary = layout["active_outer_instances"]
	var instance: Dictionary = instances["p2" if mirrored else "p1"]
	var root: Dictionary = layout["root_xuetiao"]
	var units := float(layout["scale"])
	var origin := Vector2(
		(float(root["translateX"]) + float(instance["translateX"])) / units,
		(float(root["translateY"]) + float(instance["translateY"])) / units)
	return Transform2D(
		Vector2(float(instance["scaleX"]), 0.0),
		Vector2(0.0, float(instance["scaleY"])),
		origin)
