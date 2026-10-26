extends "res://tests/nested_filter_diagnostic.gd"
# Preserve the pinned scene/production allocation and change diagnostic materials only.
const NATIVE_SHADER = preload("res://tests/native_nested_filter_composite.gdshader")
var reciprocal_texture: ImageTexture
var replaced: Array[Sprite2D] = []
var group_count := 0

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2)
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	assert(fixture.production_admitted == false and fixture.cpu_arithmetic_passed == true)
	var values: Array = fixture.native_reciprocals
	assert(values.size() == 256 and values[0] == 0)
	var bytes := PackedByteArray()
	bytes.resize(256 * 4)
	for i in 256:
		assert(is_finite(float(values[i])) and (i == 0 or values[i] > 0))
		bytes.encode_float(i * 4, float(values[i]))
	var image := Image.create_from_data(256, 1, false, Image.FORMAT_RF, bytes)
	reciprocal_texture = ImageTexture.create_from_image(image)
	assert(reciprocal_texture.get_image().get_data() == bytes)
	node_added.connect(_replace_material)
	process_frame.connect(_verify_materials)
	super._initialize()

func _replace_material(node: Node) -> void:
	if not node is Sprite2D or not node.material is ShaderMaterial:
		return
	var previous: ShaderMaterial = node.material
	if previous.shader.resource_path != "res://tests/nested_filter_composite.gdshader":
		return
	var material := ShaderMaterial.new()
	material.shader = NATIVE_SHADER
	for parameter in ["opacity_multiplier", "post_mul", "post_add"]:
		material.set_shader_parameter(parameter, previous.get_shader_parameter(parameter))
	material.set_shader_parameter("native_reciprocals", reciprocal_texture)
	node.material = material
	replaced.append(node)
	if node.name == "Composite":
		group_count += 1
	assert(replaced.size() <= 336)
	if replaced.size() == 336:
		assert(group_count == 96)
		print("NATIVE_CXFORM_BINDINGS_OK sprites=336 groups=96 production_admitted=false")

func _verify_materials() -> void:
	for sprite in replaced:
		assert(is_instance_valid(sprite) and sprite.material.shader == NATIVE_SHADER)
