class_name RenderSurface
extends Control

# Compatibility/Web has no 2D MSAA. Resolve a complete sample grid instead of
# changing bitmap filtering or relying on an unsupported viewport setting.
const RESOLVE := preload("res://sample_resolve.gdshader")
const ONLINE_LOBBY := preload("res://online_lobby.gd")
var source_viewport: SubViewport
var presentation: TextureRect
var game: Control
var online_lobby: OnlineLobby
var sample_grid: int = 4
var texture_limit: int = 0
var rules: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/config/config.json")).rendering


func _ready() -> void:
	if OS.has_feature("web"):
		texture_limit = int(JavaScriptBridge.eval("(() => { const gl = document.getElementById('canvas').getContext('webgl2'); const viewport = gl.getParameter(gl.MAX_VIEWPORT_DIMS); return Math.min(gl.getParameter(gl.MAX_TEXTURE_SIZE), gl.getParameter(gl.MAX_RENDERBUFFER_SIZE), viewport[0], viewport[1]); })()"))
		assert(texture_limit > 0, "WebGL render limits unavailable")
	source_viewport = SubViewport.new()
	source_viewport.disable_3d = true
	source_viewport.handle_input_locally = false
	source_viewport.size_2d_override_stretch = true
	source_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(source_viewport)
	presentation = TextureRect.new()
	presentation.mouse_filter = Control.MOUSE_FILTER_IGNORE
	presentation.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	presentation.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	presentation.texture = source_viewport.get_texture()
	var resolve := ShaderMaterial.new()
	resolve.shader = RESOLVE
	presentation.material = resolve
	add_child(presentation)
	presentation.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	resized.connect(_resize_surface)
	get_viewport().size_changed.connect(_resize_surface)
	_resize_surface()
	game = _create_game_scene()
	online_lobby = ONLINE_LOBBY.new()
	online_lobby.name = "OnlineLobby"
	online_lobby.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	online_lobby.z_index = 1000
	add_child(online_lobby)
	online_lobby.configure(self, game)


func _create_game_scene() -> Control:
	var scene: Control = preload("res://main.tscn").instantiate()
	source_viewport.add_child(scene)
	scene.session.render_quality_changed.connect(apply_quality)
	apply_quality(scene.session.render_quality)
	return scene


func recreate_game_scene() -> Control:
	if game != null and is_instance_valid(game):
		game.set_physics_process(false)
		game.queue_free()
	game = _create_game_scene()
	if online_lobby != null and is_instance_valid(online_lobby):
		online_lobby.configure(self, game)
	return game


func apply_quality(quality: String) -> void:
	assert(rules.sample_grid.has(quality), "Unsupported source quality: " + quality)
	sample_grid = int(rules.sample_grid[quality])
	_resize_surface()


func _resize_surface() -> void:
	if source_viewport == null or presentation == null:
		return
	var logical_size := Vector2i(size).max(Vector2i.ONE)
	# ViewportTexture.get_size() includes the stretch a second time for Window
	# viewports. Map the actual canvas rectangle to pixels instead; this also
	# excludes aspect-ratio letterboxing from the sampling target.
	var physical_size := Vector2i(get_viewport().get_final_transform().basis_xform(size)).max(Vector2i.ONE)
	if texture_limit > 0:
		# Keep the same presentation resolution at every quality, including when
		# a high-DPI canvas would exceed the WebGL attachment size limit at HIGH.
		var maximum_grid := int(rules.sample_grid.values().max())
		var maximum_output := texture_limit / maximum_grid
		var fit := minf(1.0, float(maximum_output) / float(maxi(physical_size.x, physical_size.y)))
		physical_size = Vector2i(Vector2(physical_size) * fit).max(Vector2i.ONE)
	source_viewport.size_2d_override = logical_size
	source_viewport.size = physical_size * sample_grid
	presentation.material.set_shader_parameter("sample_grid", sample_grid)
	presentation.material.set_shader_parameter("output_size", Vector2(physical_size))


func _input(event: InputEvent) -> void:
	if source_viewport != null:
		if online_lobby != null and online_lobby.blocks_game_input(event):
			return
		# Events already use the root's logical canvas coordinates. The child
		# viewport exposes the same coordinates regardless of raster resolution.
		source_viewport.push_input(event, true)
