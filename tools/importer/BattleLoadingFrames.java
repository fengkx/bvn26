import com.eclipsesource.json.JsonArray;
import com.eclipsesource.json.JsonObject;
import com.jpexs.decompiler.flash.SWF;
import com.jpexs.decompiler.flash.exporters.commonshape.Matrix;
import com.jpexs.decompiler.flash.tags.DefineSpriteTag;
import com.jpexs.decompiler.flash.timeline.DepthState;
import com.jpexs.decompiler.flash.timeline.Timeline;
import com.jpexs.decompiler.flash.types.RECT;
import java.awt.Color;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.FileInputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.TreeMap;
import java.util.function.IntPredicate;
import javax.imageio.ImageIO;

/** Bake Flash vector layers at stage resolution and retain per-player placements in twips. */
class BattleLoadingFrames {
    private final SWF movie;
    private final Path output;
    private final Timeline loading;
    private final Matrix stage;
    private final Color transparent = new Color(0, true);

    BattleLoadingFrames(String source, Path output) throws Exception {
        try (var input = new FileInputStream(source)) {
            movie = new SWF(input, false);
        }
        this.output = Files.createDirectories(output);
        loading = sprite(1989);
        var root = movie.getTimeline();
        var placement = root.getFrame(root.getFrameWithLabel("游戏场景")).layers.values().stream()
            .filter(d -> d.characterId == 1989).findFirst().orElseThrow();
        stage = new Matrix(placement.matrix);
    }

    private Timeline sprite(int id) {
        return ((DefineSpriteTag)movie.getCharacter(id)).getTimeline();
    }

    private BufferedImage render(Timeline clip, int frame, RECT bounds, Matrix transform, Color bg) {
        return SWF.frameToImageGet(clip, frame, 0, null, 0, bounds, transform, null, bg,
            1, true, 1).getBufferedImage();
    }

    private JsonArray save(BufferedImage image) throws Exception {
        int left = image.getWidth(), top = image.getHeight(), right = -1, bottom = -1;
        for (int y = 0; y < image.getHeight(); y++) {
            for (int x = 0; x < image.getWidth(); x++) {
                if ((image.getRGB(x, y) >>> 24) == 0) continue;
                left = Math.min(left, x);
                right = Math.max(right, x);
                top = Math.min(top, y);
                bottom = Math.max(bottom, y);
            }
        }
        if (right < left) return new JsonArray();
        var bytes = new ByteArrayOutputStream();
        ImageIO.write(image.getSubimage(left, top, right-left+1, bottom-top+1), "png", bytes);
        var png = bytes.toByteArray();
        var name = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(png), 0, 12);
        var file = output.resolve(name + ".png");
        if (!Files.exists(file)) Files.write(file, png);
        return new JsonArray().add(name).add(left).add(top);
    }

    private JsonArray layer(int frame, IntPredicate keep, Color bg) throws Exception {
        var f = loading.getFrame(frame);
        var original = f.layers;
        f.layers = new TreeMap<>(original);
        f.layers.keySet().removeIf(depth -> !keep.test(depth));
        try {
            return save(render(loading, frame, movie.displayRect, stage, bg));
        } finally {
            f.layers = original;
        }
    }

    private JsonArray placement(DepthState d) {
        if (d == null) return new JsonArray();
        return new JsonArray().add((int)stage.translateX + d.matrix.translateX)
            .add((int)stage.translateY + d.matrix.translateY).add(new Matrix(d.matrix).scaleX < 0);
    }

    private void export() throws Exception {
        var sound = (com.jpexs.decompiler.flash.tags.DefineSoundTag)movie.getCharacter(loading.getFrame(3).sounds.get(0));
        if (sound.getSoundFormatId() != 2) throw new IllegalStateException("Expected MP3 loading cue");
        try (var out = Files.newOutputStream(output.resolve("entrance.mp3"))) {
            for (var part : sound.getRawSoundData()) out.write(part.getRangeData());
        }
        var frames = new JsonArray();
        for (int i = 0; i < 184; i++) {
            var f = loading.getFrame(i);
            frames.add(new JsonObject()
                .add("background", layer(i, d -> d < 6, Color.BLACK))
                .add("front", layer(i, d -> d > 10 && d != 16, transparent))
                .add("p1", placement(f.layers.get(10))).add("p2", placement(f.layers.get(6))));
        }
        var meter = sprite(1900);
        var meterFrames = new JsonArray();
        var meterStage = stage.concatenate(new Matrix(loading.getFrame(0).layers.get(16).matrix));
        for (int i = 0; i < meter.getFrameCount(); i++)
            meterFrames.add(save(render(meter, i, movie.displayRect, meterStage, transparent)));
        var meterFace = meter.getFrame(0);
        var complete = new TreeMap<>(meterFace.layers);
        meterFace.layers.keySet().removeIf(depth -> depth != 3);
        var fill = save(render(meter, 0, movie.displayRect, meterStage, transparent));
        meterFace.layers = complete;
        meterFace.layers.remove(3);
        var empty = save(render(meter, 0, movie.displayRect, meterStage, transparent));
        var banners = new JsonObject();
        var portraits = sprite(1983);
        var authored = portraits.getFrames().stream().map(f -> new TreeMap<>(f.layers)).toList();
        for (var f : portraits.getFrames()) {
            if (f.labels.isEmpty()) continue;
            for (var other : portraits.getFrames()) other.layers = authored.get(f.frame);
            movie.clearImageCache();
            var banner = render(sprite(1985), 0, new RECT(0,10600,0,1960),
                Matrix.getTranslateInstance(200,120), transparent);
            banners.add(f.labels.get(0), save(banner));
        }
        var data = new JsonObject().add("frames", frames).add("portraits", banners)
            .add("meter", meterFrames).add("empty_meter", empty).add("fill", fill)
            .add("skip", loading.getFrameWithLabel("skip")+1).add("fps", (double)movie.frameRate);
        Files.writeString(output.resolve("loading.json"), data.toString());
    }

    public static void main(String[] args) throws Exception {
        new BattleLoadingFrames(args[0], Path.of(args[1])).export();
    }
}
