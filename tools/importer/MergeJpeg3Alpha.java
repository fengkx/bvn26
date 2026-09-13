import java.awt.image.BufferedImage;
import java.io.File;
import javax.imageio.ImageIO;

/** Rebuild a JPEG3 bitmap from its exported JPEG and alpha sidecar. */
class MergeJpeg3Alpha {
    public static void main(String[] args) throws Exception {
        if (args.length != 3) {
            throw new IllegalArgumentException("Usage: <rgb.jpg> <alpha.png> <output.png>");
        }
        BufferedImage rgb = ImageIO.read(new File(args[0]));
        BufferedImage alpha = ImageIO.read(new File(args[1]));
        if (rgb == null || alpha == null || !alpha.getColorModel().hasAlpha()) {
            throw new IllegalArgumentException("JPEG3 source requires RGB and alpha images");
        }
        if (rgb.getWidth() != alpha.getWidth() || rgb.getHeight() != alpha.getHeight()) {
            throw new IllegalArgumentException("JPEG3 RGB and alpha dimensions differ");
        }

        BufferedImage rgba = new BufferedImage(rgb.getWidth(), rgb.getHeight(), BufferedImage.TYPE_INT_ARGB);
        for (int y = 0; y < rgb.getHeight(); y++) {
            for (int x = 0; x < rgb.getWidth(); x++) {
                int color = rgb.getRGB(x, y);
                int alphaValue = alpha.getRGB(x, y) >>> 24;
                rgba.setRGB(x, y, (alphaValue << 24) | (color & 0x00ffffff));
            }
        }
        if (!ImageIO.write(rgba, "png", new File(args[2]))) {
            throw new IllegalStateException("No PNG writer is available");
        }
    }
}
