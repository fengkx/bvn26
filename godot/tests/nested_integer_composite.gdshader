shader_type canvas_item;
render_mode blend_disabled;
#include "res://tests/normal_composition.gdshaderinc"
uniform sampler2D screen_texture : hint_screen_texture, filter_nearest, repeat_disable;
uniform int opacity_multiplier = 256;
void fragment() {
    ivec4 source = ivec4(round(texture(TEXTURE, UV) * 255.0));
    ivec4 back = ivec4(round(texture(screen_texture, SCREEN_UV) * 255.0));
    COLOR = vec4(flash_normal_over(back, flash_bitmap_opacity(source, opacity_multiplier))) / 255.0;
}
