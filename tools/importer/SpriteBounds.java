import com.jpexs.decompiler.flash.SWF;
import com.jpexs.decompiler.flash.tags.DefineSpriteTag;
import com.jpexs.decompiler.flash.types.RECT;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.util.ArrayList;
import com.jpexs.decompiler.flash.tags.Tag;
import com.jpexs.decompiler.flash.tags.ShowFrameTag;
import com.jpexs.decompiler.flash.tags.PlaceObject2Tag;

/** Use the rasterizer's bounds so exported frames retain their registration point. */
class SpriteBounds {
    public static void main(String[] args) throws Exception {
        try (FileInputStream input = new FileInputStream(args[0])) {
            SWF swf = new SWF(input, false);
            DefineSpriteTag sprite = (DefineSpriteTag) swf.getCharacter(Integer.parseInt(args[1]));
            RECT bounds = sprite.getRect();
            System.out.printf("[%d,%d,%d,%d]%n", bounds.Xmin, bounds.Ymin, bounds.Xmax, bounds.Ymax);
            if (args.length == 3) {
                // Keep original image bytes and fonts; only trim a temporary copy.
                boolean afterFirstFrame = false;
                ArrayList<Tag> remove = new ArrayList<>();
                for (Tag tag : sprite.getTags()) {
                    if (afterFirstFrame || (tag instanceof PlaceObject2Tag
                            && "skk".equals(((PlaceObject2Tag) tag).name))) {
                        remove.add(tag);
                    }
                    if (tag instanceof ShowFrameTag) afterFirstFrame = true;
                }
                for (Tag tag : remove) sprite.removeTag(tag);
                sprite.frameCount = 1;
                sprite.setModified(true);
                try (FileOutputStream output = new FileOutputStream(args[2])) {
                    swf.saveTo(output);
                }
            }
        }
    }
}
