// Premultiplied byte operations. Diagnostic only until production admission.
ivec4 flash_normal_over(ivec4 back, ivec4 front) {
    return front + (back * (256 - front.a)) / 256;
}
ivec4 flash_bitmap_opacity(ivec4 pixel, int multiplier) {
    return pixel * multiplier / 256;
}
ivec4 flash_vector_opacity(ivec4 pixel, ivec3 color, int multiplier) {
    int alpha = pixel.a * multiplier / 256;
    return ivec4(color * (alpha + 1) / 256, alpha);
}
