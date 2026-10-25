extends "res://tests/integer_shadow_rows.gd"

func _source(spec: Dictionary) -> Sprite2D:
	assert(spec.width == 64 and spec.height == 64 and spec.source_row.size() == 64)
	# The source authors the same row on y24..40; use its native input readback,
	# never filtered output, to isolate filter math from source PNG decoding.
	var bytes := PackedByteArray()
	bytes.resize(64 * 64 * 4)
	for y in range(24, 41):
		for x in 64:
			for channel in 4:
				bytes[(y*64+x)*4+channel] = spec.source_row[x][channel]
	var texture := ImageTexture.create_from_image(Image.create_from_data(64, 64, false, Image.FORMAT_RGBA8, bytes))
	assert(texture.get_image().get_data() == bytes)
	var sprite := Sprite2D.new()
	sprite.centered = false
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	sprite.texture = texture
	var material := ShaderMaterial.new()
	material.shader = RAW
	sprite.material = material
	return sprite
