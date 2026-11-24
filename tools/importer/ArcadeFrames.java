import com.jpexs.decompiler.flash.SWF;
import com.jpexs.decompiler.flash.exporters.commonshape.Matrix;
import com.jpexs.decompiler.flash.tags.DefineSpriteTag;
import com.jpexs.decompiler.flash.timeline.Timeline;
import java.awt.Color;
import java.io.FileInputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import javax.imageio.ImageIO;

/** Render root labels at the original stage registration, with the parent stopped. */
class ArcadeFrames {
    private final SWF swf;
    private final Path output;

    ArcadeFrames(String source, Path output) throws Exception {
        try (var input = new FileInputStream(source)) {
            swf = new SWF(input, false);
        }
        this.output = output;
    }

    private Timeline sprite(int id) {
        return ((DefineSpriteTag) swf.getCharacter(id)).getTimeline();
    }

    private void render(String name, String label, int length) throws Exception {
        Path directory = Files.createDirectories(output.resolve(name));
        var root = swf.getTimeline();
        int frame = root.getFrameWithLabel(label);
        for (int tick = 0; tick < length; tick++) {
            var image = SWF.frameToImageGet(root, frame, tick, null, 0, swf.displayRect,
                new Matrix(), null, Color.BLACK, 1, true, 1);
            ImageIO.write(image.getBufferedImage(), "png", directory.resolve((tick + 1) + ".png").toFile());
        }
    }

    public static void main(String[] args) throws Exception {
        var movie = new ArcadeFrames(args[0], Path.of(args[1]));
        for (var frame : movie.sprite(2050).getFrames()) frame.layers.remove(1); // Portal link
        for (var frame : movie.sprite(2074).getFrames()) frame.layers.remove(7);
        for (var frame : movie.sprite(2032).getFrames()) frame.layers.remove(16);
        movie.render("tutorial", "HOWTOPLAY", 1260);
        movie.render("continue", "继续", 30);
        movie.render("gameover", "gameover", 150);
        movie.render("ending", "congratution", 318);
        var portraits = movie.sprite(1346);
        var authored = portraits.getFrames().stream().map(frame -> new java.util.TreeMap<>(frame.layers)).toList();
        for (String line : Files.readAllLines(Path.of(args[2]))) {
            String[] pair = line.split("\t");
            var portrait = authored.get(portraits.getFrameWithLabel(pair[0]));
            // The source load handler stops the portrait timeline at the selected label.
            for (var frame : portraits.getFrames()) frame.layers = portrait;
            movie.swf.clearImageCache();
            movie.render("win-" + pair[1], "YOUWIN", 24);
        }
    }
}
