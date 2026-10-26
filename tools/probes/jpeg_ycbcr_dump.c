/* Diagnostic only: expose libjpeg's decoded component bytes before RGB conversion. */
#include <stdio.h>
#include <stdlib.h>
#include <jpeglib.h>

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    FILE *input = fopen(argv[1], "rb");
    if (!input) return 2;
    struct jpeg_decompress_struct decoder;
    struct jpeg_error_mgr error;
    decoder.err = jpeg_std_error(&error);
    jpeg_create_decompress(&decoder);
    jpeg_stdio_src(&decoder, input);
    jpeg_read_header(&decoder, TRUE);
    if (decoder.jpeg_color_space != JCS_YCbCr || decoder.num_components != 3) return 3;
    decoder.out_color_space = JCS_YCbCr;
    decoder.dct_method = JDCT_ISLOW;
    decoder.do_fancy_upsampling = FALSE;
    jpeg_start_decompress(&decoder);
    fprintf(stdout, "P6\n%u %u\n255\n", decoder.output_width, decoder.output_height);
    JSAMPARRAY row = (*decoder.mem->alloc_sarray)((j_common_ptr)&decoder, JPOOL_IMAGE,
                                                decoder.output_width * 3, 1);
    while (decoder.output_scanline < decoder.output_height) {
        jpeg_read_scanlines(&decoder, row, 1);
        if (fwrite(row[0], 3, decoder.output_width, stdout) != decoder.output_width) return 4;
    }
    jpeg_finish_decompress(&decoder);
    jpeg_destroy_decompress(&decoder);
    fclose(input);
    return 0;
}
