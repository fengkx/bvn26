/* Diagnostic coefficient-domain reconstruction; no native RGB is input. */
#include <stdio.h>
#include <stdlib.h>
#include <jpeglib.h>

int main(int argc, char **argv) {
    if (argc != 4) return 2;
    int scale = atoi(argv[3]);
    if (scale != 1 && scale != 2) return 2;
    FILE *input = fopen(argv[1], "rb");
    if (!input) return 2;
    struct jpeg_decompress_struct decoder;
    struct jpeg_error_mgr error;
    decoder.err = jpeg_std_error(&error);
    jpeg_create_decompress(&decoder);
    jpeg_stdio_src(&decoder, input);
    jpeg_read_header(&decoder, TRUE);
    if (decoder.jpeg_color_space != JCS_YCbCr || decoder.num_components != 3) return 3;
    decoder.raw_data_out = TRUE;
    decoder.dct_method = JDCT_ISLOW;
    decoder.scale_num = scale;
    decoder.scale_denom = 1;
    jpeg_start_decompress(&decoder);
    JSAMPIMAGE planes = (*decoder.mem->alloc_small)((j_common_ptr)&decoder, JPOOL_IMAGE, 3 * sizeof(JSAMPARRAY));
    FILE *files[3];
    unsigned written[3] = {0, 0, 0};
    int rows[3];
    for (int c = 0; c < 3; c++) {
        jpeg_component_info *component = &decoder.comp_info[c];
        rows[c] = component->v_samp_factor * component->DCT_v_scaled_size;
        planes[c] = (*decoder.mem->alloc_sarray)((j_common_ptr)&decoder, JPOOL_IMAGE,
                       component->width_in_blocks * component->DCT_h_scaled_size, rows[c]);
        char path[4096];
        if (snprintf(path, sizeof(path), "%s/c%d.pgm", argv[2], c) >= (int)sizeof(path)) return 2;
        files[c] = fopen(path, "wb");
        if (!files[c]) return 2;
        fprintf(files[c], "P5\n%u %u\n255\n", component->downsampled_width, component->downsampled_height);
        fprintf(stderr, "component %d: sampling %dx%d, IDCT %dx%d, plane %ux%u\n", c,
                component->h_samp_factor, component->v_samp_factor,
                component->DCT_h_scaled_size, component->DCT_v_scaled_size,
                component->downsampled_width, component->downsampled_height);
    }
    while (decoder.output_scanline < decoder.output_height) {
        if (!jpeg_read_raw_data(&decoder, planes, decoder.max_v_samp_factor * decoder.min_DCT_v_scaled_size)) return 4;
        for (int c = 0; c < 3; c++) {
            jpeg_component_info *component = &decoder.comp_info[c];
            for (int r = 0; r < rows[c] && written[c] < component->downsampled_height; r++, written[c]++) {
                if (fwrite(planes[c][r], 1, component->downsampled_width, files[c]) != component->downsampled_width) return 4;
            }
        }
    }
    for (int c = 0; c < 3; c++) fclose(files[c]);
    jpeg_finish_decompress(&decoder);
    jpeg_destroy_decompress(&decoder);
    fclose(input);
    return 0;
}
