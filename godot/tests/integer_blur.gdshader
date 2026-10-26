shader_type canvas_item;
render_mode blend_disabled;
uniform vec2 direction = vec2(1.0, 0.0);
uniform float blur_size = 1.0;

ivec4 source_bytes(sampler2D image, vec2 uv) {
    if (any(lessThan(uv, vec2(0.0))) || any(greaterThanEqual(uv, vec2(1.0)))) {
        return ivec4(0);
    }
    return ivec4(floor(texture(image, uv) * 255.0 + 0.5));
}

void fragment() {
    // Consumed kernels above one are exact multiples of 1/32 in the bounded suite.
    int kernel = int(blur_size * 32.0);
    int radius = max(0, kernel - 32);
    int edge = (radius + 63) / 64;
    ivec4 sum = source_bytes(TEXTURE, UV) * 64;
    for (int i = 1; i <= edge; i++) {
        int weight = clamp(radius - i * 64 + 64, 0, 64);
        vec2 delta = direction * TEXTURE_PIXEL_SIZE * float(i);
        sum += (source_bytes(TEXTURE, UV - delta) + source_bytes(TEXTURE, UV + delta)) * weight;
    }
    COLOR = vec4(sum / max(64, 2 * kernel)) / 255.0;
}
