class_name ShadowSnapshot
extends Node2D

signal source_event(kind: String, values: Array)

const SPEC_PATH := "res://generated/main/shadow.json"
static var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(SPEC_PATH))
const TINT_SHADER := """
shader_type canvas_item;
render_mode blend_premul_alpha;
uniform vec3 offsets;
void fragment() {
	vec4 tex = texture(TEXTURE, UV);
	COLOR = vec4(clamp(tex.rgb + offsets * tex.a, vec3(0.0), vec3(tex.a)), tex.a) * COLOR.a;
}
"""

var source_alpha: float
var captured_frame: int
var bitmap_size: Vector2i
var bounds: Rect2
var source_x: float
var source_y: float
var registry: SourceCallbackRegistry
var registration: int
var bitmap: Sprite2D
var capture_viewport: SubViewport

static func should_capture(actor: FighterRuntime) -> bool:
	var counter := int(actor.get_meta("shadow_counter", spec.counter_initial)) + 1
	if counter > int(spec.counter_skip_above):
		actor.set_meta("shadow_counter", spec.counter_initial)
		return false
	actor.set_meta("shadow_counter", counter)
	return true

func capture(actor: FighterRuntime, rgb: Dictionary, callbacks: SourceCallbackRegistry, tick: int) -> void:
	set_meta("source_shadow", true)
	registry = callbacks
	captured_frame = actor.current_source_frame()
	# getBounds includes authored invisible receivers, unlike visible-pixel bounds.
	for placement: Dictionary in actor._frames[captured_frame]["display_list"]:
		var placed := _placement_bounds(actor, placement, captured_frame, actor._wrapper_transform())
		if placed.has_area():
			bounds = bounds.merge(placed) if bounds.has_area() else placed
	bitmap_size = Vector2i(int(bounds.size.x * absf(actor.scale.x)), int(bounds.size.y * absf(actor.scale.y)))
	assert(bitmap_size.x > 0 and bitmap_size.y > 0, "Invalid source BitmapData dimensions")
	source_x = SourceCoordinate.store(actor.source_x + SourceCoordinate.from_projection(bounds.position.x) * signf(actor.scale.x))
	source_y = SourceCoordinate.store(actor.source_y + SourceCoordinate.from_projection(bounds.position.y))
	position = Vector2(source_x, source_y)
	scale.x = actor.scale.x
	z_index = int(spec.layer_depth)
	capture_viewport = SubViewport.new()
	capture_viewport.size = bitmap_size
	capture_viewport.transparent_bg = true
	capture_viewport.disable_3d = true
	capture_viewport.render_target_update_mode = SubViewport.UPDATE_ONCE
	capture_viewport.handle_input_locally = false
	add_child(capture_viewport)
	var frozen := Node2D.new()
	frozen.position = -bounds.position
	capture_viewport.add_child(frozen)
	# Snapshot only the already materialized display list. Duplicating the actor
	# would copy live callbacks, collision services and sound playback.
	for child in actor.get_children():
		if child.is_queued_for_deletion() or not (child is Sprite2D or child is Polygon2D):
			continue
		frozen.add_child(child.duplicate(0))
	bitmap = Sprite2D.new()
	bitmap.centered = false
	bitmap.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	bitmap.texture = capture_viewport.get_texture()
	var shader := Shader.new()
	shader.code = TINT_SHADER
	var tint := ShaderMaterial.new()
	tint.shader = shader
	tint.set_shader_parameter("offsets", Vector3(float(rgb.get("R", 0)), float(rgb.get("G", 0)), float(rgb.get("B", 0))) / 255.0)
	bitmap.material = tint
	add_child(bitmap)
	source_alpha = float(spec.alpha_start)
	registration = registry.register(self, "fade", tick)
	source_event.emit("spawn", [captured_frame, source_x, source_y, scale.x * 100, bitmap_size.x, bitmap_size.y, source_alpha,
		bounds.position.x, bounds.position.y, bounds.end.x, bounds.end.y])

func _placement_bounds(actor: FighterRuntime, placement: Dictionary, frame: int, parent_matrix: Transform2D) -> Rect2:
	var definition: Dictionary = actor._definitions.get(int(placement.character_id), {})
	if definition.is_empty():
		return Rect2()
	var matrix := parent_matrix * actor._placement_transform(placement)
	# FP32 concatenates integer-twip translations before transforming the shape.
	# Rounding only the final bounds loses a twip in the aerial snapshot.
	matrix.origin = Vector2(roundf(matrix.origin.x * 20), roundf(matrix.origin.y * 20)) / 20
	if definition.has("shape_bounds_twips"):
		var shape: Dictionary = definition.shape_bounds_twips
		var local := Rect2(Vector2(shape.Xmin, shape.Ymin) / 20, Vector2(shape.Xmax - shape.Xmin, shape.Ymax - shape.Ymin) / 20)
		var transformed := actor._transform_rect(matrix, local)
		var minimum := Vector2(roundf(transformed.position.x * 20), roundf(transformed.position.y * 20)) / 20
		var maximum := Vector2(roundf(transformed.end.x * 20), roundf(transformed.end.y * 20)) / 20
		return Rect2(minimum, maximum - minimum)
	if definition.type != "DefineSpriteTag":
		return Rect2()
	var frames: Array = definition.get("display_list_frames", [])
	var local_frame := actor._nested_frame(placement, frame, frames.size())
	if placement.get("name", "") == spec.controller.instance:
		if not actor.ai_predicate_context.use_ai:
			return Rect2()
		local_frame = int(spec.controller.cpu_frame)
	var children: Array = frames[local_frame - 1] if not frames.is_empty() else definition.get("first_frame_display_list", [])
	var result := Rect2()
	for child: Dictionary in children:
		var child_bounds := _placement_bounds(actor, child, local_frame, matrix)
		if child_bounds.has_area():
			result = result.merge(child_bounds) if result.has_area() else child_bounds
	return result

func fade() -> void:
	# FP32 stores _alpha as a signed 8.8 multiplier, truncating toward zero.
	source_alpha = float(int((source_alpha - float(spec.alpha_lose)) * 256.0 / 100.0)) * 100.0 / 256.0
	source_event.emit("fade", [source_alpha])
	bitmap.modulate.a = maxf(source_alpha / 100.0, 0)
	if source_alpha <= 0:
		dispose()

func dispose() -> void:
	if registry != null:
		registry.unregister(registration)
		registry = null
	if get_parent() != null:
		get_parent().remove_child(self)
	queue_free()

func _exit_tree() -> void:
	if registry != null:
		registry.unregister(registration)
		registry = null
