shader_type canvas_item;
render_mode blend_disabled;
uniform int operation = 0;
uniform vec2 direction = vec2(1.0, 0.0);
uniform float blur_size = 1.0;
uniform sampler2D original_texture : filter_nearest, repeat_disable;
uniform vec4 glow_color = vec4(1.0);
uniform float glow_strength = 1.0;
uniform vec4 row_r = vec4(1.0, 0.0, 0.0, 0.0);
uniform vec4 row_g = vec4(0.0, 1.0, 0.0, 0.0);
uniform vec4 row_b = vec4(0.0, 0.0, 1.0, 0.0);
uniform vec4 row_a = vec4(0.0, 0.0, 0.0, 1.0);
uniform vec4 offsets = vec4(0.0);

vec4 sample_zero(sampler2D image, vec2 uv) {
    if (any(lessThan(uv, vec2(0.0))) || any(greaterThanEqual(uv, vec2(1.0)))) { return vec4(0.0); }
    return texture(image, uv);
}

void fragment() {
    vec4 pixel = texture(TEXTURE, UV);
    if (operation == 0) {
        float radius = max(0.0, (blur_size - 1.0) * 0.5);
        int edge = int(ceil(radius));
        vec4 sum = pixel;
        for (int i = 1; i <= edge; i++) {
            float weight = clamp(radius - float(i) + 1.0, 0.0, 1.0);
            vec2 delta = direction * TEXTURE_PIXEL_SIZE * float(i);
            sum += (sample_zero(TEXTURE, UV - delta) + sample_zero(TEXTURE, UV + delta)) * weight;
        }
        pixel = floor(clamp(sum / max(1.0, blur_size), vec4(0.0), vec4(1.0)) * 255.0 + 0.0001) / 255.0;
    } else if (operation == 1) {
        vec4 base = floor(texture(original_texture, UV) * 255.0 + 0.5);
        float alpha = clamp(pixel.a * glow_strength, 0.0, 1.0) * glow_color.a;
        vec4 glow = floor(vec4(glow_color.rgb * alpha, alpha) * 255.0 + 0.5);
        // The source is composited over the glow in Flash's 8-bit cache.
        pixel = (base + floor(glow * (256.0 - base.a) / 256.0)) / 255.0;
    } else if (operation == 2) {
        vec4 straight = pixel.a > 0.0 ? vec4(pixel.rgb / pixel.a, pixel.a) : vec4(0.0);
        pixel = clamp(vec4(dot(row_r, straight), dot(row_g, straight), dot(row_b, straight), dot(row_a, straight)) + offsets, vec4(0.0), vec4(1.0));
        pixel.rgb *= pixel.a;
    }
    COLOR = pixel;
}
