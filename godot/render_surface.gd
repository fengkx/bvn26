class_name RenderSurface
extends Control

# Compatibility/Web has no 2D MSAA. Resolve a complete sample grid instead of
# changing bitmap filtering or relying on an unsupported viewport setting.
const RESOLVE := preload("res://sample_resolve.gdshader")
const ONLINE_LOBBY := preload("res://online_lobby.gd")
# Flash stage is 600×400. HIGH sample_grid is 4 → 2400×1600 (3.84 MP). Texture
# size clamps only prevent GPU OOM; this budget keeps HiDPI web from scheduling
# ~34 MP supersamples that miss 30 Hz. Keep aligned with tools/web_raster_budget.py.
# Tradeoff: the cap shrinks physical_output (composite grid). On a large HiDPI
# canvas, HIGH can resolve to ~600×400 then upscale — coarser than budgeted
# MEDIUM (~1200×800) — while still running sample_grid² taps per fragment.
# Lower raster MP does not by itself prove a sustained 30 Hz.
const WEB_RASTER_PIXEL_BUDGET: int = 3_840_000
# Full-screen effects can also allocate a screen copy at this raster size.
# On iOS, bound each of those targets to the 600×400 stage at a 2× sample grid.
const IOS_WEB_RASTER_PIXEL_BUDGET: int = 960_000
const IOS_WEB_MAX_SAMPLE_GRID: int = 2
var source_viewport: SubViewport
var presentation: TextureRect
var game: Control
var online_lobby: OnlineLobby
var sample_grid: int = 4
var web_raster_pixel_budget: int = 0
var _ios_web := false
var texture_limit: int = 0
var physical_output: Vector2i = Vector2i.ONE
var raster_size: Vector2i = Vector2i.ONE
var held_keys: Dictionary = {}
var rules: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/config/config.json")).rendering


func _ready() -> void:
	# Web keyup is canvas-scoped; moving focus to the toolbar can lose it.
	get_window().focus_exited.connect(_release_held_keys)
	if OS.has_feature("web"):
		texture_limit = int(JavaScriptBridge.eval("(() => { const gl = document.getElementById('canvas').getContext('webgl2'); const viewport = gl.getParameter(gl.MAX_VIEWPORT_DIMS); return Math.min(gl.getParameter(gl.MAX_TEXTURE_SIZE), gl.getParameter(gl.MAX_RENDERBUFFER_SIZE), viewport[0], viewport[1]); })()"))
		assert(texture_limit > 0, "WebGL render limits unavailable")
		var browser := JavaScriptBridge.get_interface("window")
		_ios_web = browser != null and browser.bvnAppleMobile == true
		web_raster_pixel_budget = IOS_WEB_RASTER_PIXEL_BUDGET if _ios_web else WEB_RASTER_PIXEL_BUDGET
		if _ios_web:
			sample_grid = mini(sample_grid, IOS_WEB_MAX_SAMPLE_GRID)
	source_viewport = SubViewport.new()
	source_viewport.disable_3d = true
	source_viewport.handle_input_locally = false
	source_viewport.size_2d_override_stretch = true
	source_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	if _ios_web:
		source_viewport.set_meta("clip_offscreen_caches", true)
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
	if OS.has_feature("web") and JavaScriptBridge.eval("typeof window.bvnTouchRegister === 'function'"):
		add_child(preload("res://web_touch_input.gd").new())


func _create_game_scene(presentation_only: bool = false) -> Control:
	var scene: Control = preload("res://main.tscn").instantiate()
	if presentation_only: scene.prepare_presentation_only()
	source_viewport.add_child(scene)
	scene.session.render_quality_changed.connect(apply_quality)
	apply_quality(scene.session.render_quality)
	return scene


func recreate_game_scene(presentation_only: bool = false) -> Control:
	if game != null and is_instance_valid(game):
		game.set_physics_process(false)
		game.queue_free()
	game = _create_game_scene(presentation_only)
	if online_lobby != null and is_instance_valid(online_lobby):
		online_lobby.configure(self, game)
	return game


func apply_quality(quality: String) -> void:
	assert(rules.sample_grid.has(quality), "Unsupported source quality: " + quality)
	sample_grid = int(rules.sample_grid[quality])
	if _ios_web:
		sample_grid = mini(sample_grid, IOS_WEB_MAX_SAMPLE_GRID)
	_resize_surface()


static func fit_physical_to_raster_budget(physical_size: Vector2i, grid: int, pixel_budget: int) -> Vector2i:
	var width := maxi(physical_size.x, 1)
	var height := maxi(physical_size.y, 1)
	var safe_grid := maxi(grid, 1)
	var safe_budget := maxi(pixel_budget, 1)
	var raster_pixels := float(width) * float(height) * float(safe_grid * safe_grid)
	if raster_pixels <= float(safe_budget):
		return Vector2i(width, height)
	var scale := sqrt(float(safe_budget) / raster_pixels)
	return Vector2i(Vector2(width, height) * scale).max(Vector2i.ONE)


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
		var maximum_grid := IOS_WEB_MAX_SAMPLE_GRID if _ios_web else int(rules.sample_grid.values().max())
		var maximum_output := texture_limit / maximum_grid
		var fit := minf(1.0, float(maximum_output) / float(maxi(physical_size.x, physical_size.y)))
		physical_size = Vector2i(Vector2(physical_size) * fit).max(Vector2i.ONE)
	if web_raster_pixel_budget > 0:
		# Perf budget, not an OOM clamp: cap physical_size * sample_grid megapixels.
		# physical_output below is this post-budget composite size.
		physical_size = fit_physical_to_raster_budget(physical_size, sample_grid, web_raster_pixel_budget)
	physical_output = physical_size
	raster_size = physical_size * sample_grid
	source_viewport.size_2d_override = logical_size
	source_viewport.size = raster_size
	presentation.material.set_shader_parameter("sample_grid", sample_grid)
	presentation.material.set_shader_parameter("output_size", Vector2(physical_size))


func _input(event: InputEvent) -> void:
	if event is InputEventKey:
		var code: int = event.physical_keycode if event.physical_keycode != KEY_NONE else event.keycode
		if event.pressed:
			held_keys[code] = event.duplicate()
		else:
			held_keys.erase(code)
	if source_viewport != null:
		if online_lobby != null and online_lobby.blocks_game_input(event):
			return
		# Events already use the root's logical canvas coordinates. The child
		# viewport exposes the same coordinates regardless of raster resolution.
		source_viewport.push_input(event, true)


func _release_held_keys() -> void:
	var releases := held_keys.values()
	held_keys.clear()
	for event: InputEventKey in releases:
		event.pressed = false
		event.echo = false
		Input.parse_input_event(event)
	Input.flush_buffered_events()
