shader_type canvas_item;
render_mode blend_disabled;
uniform sampler2D source_texture : filter_nearest, repeat_disable;
uniform sampler2D sample_metadata : filter_nearest, repeat_disable;
uniform vec2 buffer_size;
uniform vec2 source_size;

void vertex() {
    // The diagnostic gate admits identity axes only. Expand raster coverage to
    // complete destination pixels; the fragment applies authored area coverage.
    vec2 point = (MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).xy;
    vec2 snapped = mix(floor(point), ceil(point), step(vec2(0.5), UV));
    VERTEX += snapped - point;
}

vec4 source_byte(vec2 coordinate) {
    vec2 pixel = clamp(coordinate, vec2(0.0), source_size - vec2(1.0));
    vec4 value = floor(texture(source_texture, (pixel + vec2(0.5)) / source_size) * 255.0 + 0.5);
    value.rgb = floor(value.rgb * (value.a + 1.0) / 256.0);
    return value;
}

void fragment() {
    vec4 metadata = texture(sample_metadata, FRAGCOORD.xy / buffer_size);
    vec2 base = floor(metadata.xy);
    vec2 fraction = floor(fract(metadata.xy) * 256.0);
    float x = fraction.x; float y = fraction.y;
    vec4 a = source_byte(base);
    vec4 b = source_byte(base + vec2(1.0, 0.0));
    vec4 c = source_byte(base + vec2(0.0, 1.0));
    vec4 d = source_byte(base + vec2(1.0, 1.0));
    vec4 result;
    if (metadata.b < 0.5) {
        float w0 = floor((256.0-x)*(256.0-y)/256.0);
        float w1 = floor(x*(256.0-y)/256.0);
        float w2 = floor((256.0-x)*y/256.0);
        result = floor((a*w0+b*w1+c*w2+d*(256.0-w0-w1-w2))/256.0);
    } else if (metadata.b < 1.5) {
        vec4 left = floor((a*(256.0-y)+c*y)/256.0);
        vec4 right = floor((b*(256.0-y)+d*y)/256.0);
        result = floor((left*(256.0-x)+right*x)/256.0);
    } else {
        vec4 top = floor((a*(256.0-x)+b*x)/256.0);
        vec4 bottom = floor((c*(256.0-x)+d*x)/256.0);
        result = floor((top*(256.0-y)+bottom*y)/256.0);
    }
    COLOR = floor(result * metadata.a + 0.0001) / 255.0;
}
