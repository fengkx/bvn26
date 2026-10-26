shader_type canvas_item;
render_mode blend_disabled;
#include "res://tests/normal_composition.gdshaderinc"
uniform sampler2D screen_texture : hint_screen_texture, filter_nearest, repeat_disable;
uniform int opacity_multiplier = 256;
uniform vec3 post_mul = vec3(1.0);
uniform vec3 post_add = vec3(0.0);
void fragment() {
    vec4 pixel = texture(TEXTURE, UV);
    // Retain production post-filter straight RGB CXFORM before cached opacity.
    if (pixel.a > 0.0) {
        pixel.rgb = clamp(pixel.rgb / pixel.a * post_mul + post_add, vec3(0.0), vec3(1.0)) * pixel.a;
    }
    ivec4 source = ivec4(floor(pixel * 255.0 * float(opacity_multiplier) / 256.0 + 0.0001));
    ivec4 back = ivec4(round(texture(screen_texture, SCREEN_UV) * 255.0));
    COLOR = vec4(flash_normal_over(back, source)) / 255.0;
}
