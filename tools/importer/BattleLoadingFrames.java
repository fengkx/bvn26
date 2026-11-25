import com.jpexs.decompiler.flash.SWF;
import com.jpexs.decompiler.flash.exporters.commonshape.Matrix;
import com.jpexs.decompiler.flash.tags.DefineSpriteTag;
import java.awt.Color;
import java.io.FileInputStream;
import java.nio.file.Path;
import javax.imageio.ImageIO;

/** Capture the original loading composition. The game supplies portraits and progress at runtime. */
class BattleLoadingFrames {
    public static void main(String[] args) throws Exception {
        try (var input = new FileInputStream(args[0])) {
            var movie = new SWF(input, false);
            var loading = ((DefineSpriteTag) movie.getCharacter(1989)).getTimeline();
            for (var frame : loading.getFrames()) {
                frame.layers.remove(6);
                frame.layers.remove(10);
            }
            var meter = ((DefineSpriteTag) movie.getCharacter(1900)).getTimeline();
            var root = movie.getTimeline();
            for (String state : new String[]{"full", "empty"}) {
                if (state.equals("empty")) {
                    for (var frame : meter.getFrames()) frame.layers.remove(3);
                }
                // The ActionScript loader stops its child at frame one until all steps finish.
                var first = meter.getFrame(0).layers;
                for (var frame : meter.getFrames()) frame.layers = first;
                movie.clearImageCache();
                var image = SWF.frameToImageGet(root, root.getFrameWithLabel("游戏场景"), 26,
                    null, 0, movie.displayRect, new Matrix(), null, Color.BLACK, 1, true, 1);
                ImageIO.write(image.getBufferedImage(), "png", Path.of(args[1], state + ".png").toFile());
            }
        }
    }
}
