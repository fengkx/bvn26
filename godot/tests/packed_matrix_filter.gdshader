shader_type canvas_item;
render_mode unshaded, blend_disabled;
uniform ivec4 matrix_c0;
uniform ivec4 matrix_c1;
uniform ivec4 matrix_c2;
uniform ivec4 matrix_c3;
uniform ivec4 packed_offsets;
#include "res://tests/packed_matrix.gdshaderinc"
void fragment() {
	ivec2 size = textureSize(TEXTURE, 0);
	ivec2 at = ivec2(floor(UV * vec2(size)));
	ivec4 source = ivec4(round(texelFetch(TEXTURE, at, 0) * 255.0));
	bool prefix = at.x < (size.x / 4) * 4;
	ivec4 mate = source;
	if (prefix) {
		int other = at.x + (at.x % 2 == 0 ? 1 : -1);
		mate = ivec4(round(texelFetch(TEXTURE, ivec2(other, at.y), 0) * 255.0));
	}
	COLOR = vec4(matrix_packed(source, mate, prefix, matrix_c0, matrix_c1, matrix_c2, matrix_c3, packed_offsets)) / 255.0;
}
