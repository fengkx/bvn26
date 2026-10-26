shader_type canvas_item;
render_mode blend_disabled;
#include "res://tests/normal_composition.gdshaderinc"
uniform sampler2D screen_texture : hint_screen_texture, filter_nearest, repeat_disable;
uniform int opacity_multiplier = 256;
uniform vec3 post_mul = vec3(1.0);
uniform vec3 post_add = vec3(0.0);
void fragment() {
    ivec4 source = ivec4(round(texture(TEXTURE, UV) * 255.0));
    if (post_mul != vec3(1.0) || post_add != vec3(0.0)) {
        // Flash truncates the reciprocal to 8.8 before unpremultiplication.
        int reciprocal = source.a > 0 ? 65280 / source.a : 0;
        ivec3 straight = source.rgb * reciprocal / 256;
        ivec3 multiplier = ivec3(round(post_mul * 256.0));
        ivec3 offset = ivec3(round(post_add * 255.0));
        straight = clamp(straight * multiplier / 256 + offset, ivec3(0), ivec3(255));
        source.a = source.a * opacity_multiplier / 256;
        source.rgb = straight * (source.a + 1) / 256;
    } else {
        source = flash_bitmap_opacity(source, opacity_multiplier);
    }
    ivec4 back = ivec4(round(texture(screen_texture, SCREEN_UV) * 255.0));
    COLOR = vec4(flash_normal_over(back, source)) / 255.0;
}
