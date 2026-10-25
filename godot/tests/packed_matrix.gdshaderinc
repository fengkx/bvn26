// Bounded diagnostic translation of the pinned native word arithmetic.
int matrix_floor_div(int value, int divisor) {
	return value >= 0 ? value / divisor : -((-value + divisor - 1) / divisor);
}
ivec4 matrix_high_words(ivec4 product) {
	return ivec4(matrix_floor_div(product.x, 65536), matrix_floor_div(product.y, 65536),
		matrix_floor_div(product.z, 65536), matrix_floor_div(product.w, 65536));
}
ivec4 matrix_packed(ivec4 source, ivec4 mate, bool prefix,
		ivec4 c0, ivec4 c1, ivec4 c2, ivec4 c3, ivec4 offsets) {
	int factor = source.a > 0 ? 65280 / source.a : 0;
	ivec4 values;
	if (prefix && source.a == 255 && mate.a == 255) {
		values = source * 128;
	} else if (prefix) {
		values = (source * ivec4(factor, factor, factor, 256) + ivec4(127)) / 2;
	} else {
		ivec3 straight = source.a == 255 ? source.rgb : (source.rgb * factor + ivec3(127)) / 256;
		values = ivec4(straight, source.a) * 128;
	}
	ivec4 sum = matrix_high_words(c0 * values.x) + matrix_high_words(c1 * values.y)
		+ matrix_high_words(c2 * values.z) + matrix_high_words(c3 * values.w) + offsets;
	ivec4 transformed = clamp(ivec4(matrix_floor_div(sum.x, 4), matrix_floor_div(sum.y, 4),
		matrix_floor_div(sum.z, 4), matrix_floor_div(sum.w, 4)), ivec4(0), ivec4(255));
	ivec3 product = transformed.rgb * transformed.a;
	return ivec4((product + (product >> 8) + ivec3(1)) >> 8, transformed.a);
}
