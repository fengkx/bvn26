shader_type canvas_item;
render_mode blend_disabled;
#include "res://tests/normal_composition.gdshaderinc"
#include "res://tests/native_cxform.gdshaderinc"
uniform sampler2D screen_texture : hint_screen_texture, filter_nearest, repeat_disable;
uniform sampler2D native_reciprocals : filter_nearest, repeat_disable;
uniform int opacity_multiplier = 256;
// Logical native cache extent, independently measured with generateFilterRect.
uniform int native_span_padding = 0;
uniform vec3 post_mul = vec3(1.0);
uniform vec3 post_add = vec3(0.0);
void fragment() {
    ivec4 source = ivec4(round(texture(TEXTURE, UV) * 255.0));
    if (post_mul != vec3(1.0) || post_add != vec3(0.0)) {
        // Recover the fixture's authored integer fields from normalized uniforms.
        ivec3 multiplier = ivec3(round(post_mul * 256.0));
        ivec3 offset = ivec3(round(post_add * 255.0));
        int texture_width = textureSize(TEXTURE, 0).x;
        int width = texture_width + 2 * native_span_padding;
        int x = int(floor(UV.x * float(texture_width))) + native_span_padding;
        if (width >= 16 && x < (width / 4) * 4) {
            float reciprocal = texelFetch(native_reciprocals, ivec2(source.a, 0), 0).r;
            source = native_byte_cxform(source, multiplier, offset, opacity_multiplier, reciprocal);
        } else {
            int reciprocal = source.a > 0 ? 65280 / source.a : 0;
            ivec3 straight = source.rgb * reciprocal / 256;
            straight = clamp(straight * multiplier / 256 + offset, ivec3(0), ivec3(255));
            source.a = source.a * opacity_multiplier / 256;
            source.rgb = straight * (source.a + 1) / 256;
        }
    } else {
        source = flash_bitmap_opacity(source, opacity_multiplier);
    }
    ivec4 back = ivec4(round(texture(screen_texture, SCREEN_UV) * 255.0));
    COLOR = vec4(flash_normal_over(back, source)) / 255.0;
}
