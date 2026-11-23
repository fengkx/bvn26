import com.jpexs.decompiler.flash.SWF;
import com.jpexs.decompiler.flash.tags.*;
import com.jpexs.decompiler.flash.types.RECT;
import java.io.*;
import java.util.*;
class MenuExport {
 public static void main(String[] args) throws Exception {
  SWF s=new SWF(new FileInputStream(args[0]),false);
  for(int id: new int[]{666,594,597,600,603,606,609,612,615,672}) {
   DefineSpriteTag sprite=(DefineSpriteTag)s.getCharacter(id);
   RECT r=sprite.getRect();System.out.printf("%d %d %d %d %d%n",id,r.Xmin,r.Ymin,r.Xmax,r.Ymax);
  }
  DefineSpriteTag main=(DefineSpriteTag)s.getCharacter(666);
  ArrayList<Tag> tags=new ArrayList<>(); for(Tag t:main.getTags()) tags.add(t);
  for(Tag t:tags) if(t instanceof PlaceObject2Tag) {
   PlaceObject2Tag p=(PlaceObject2Tag)t;
   // These placements belong to the original hosting portal: panel, logo and links.
   boolean portalOverlay = Set.of(646, 648, 652, 655, 665).contains(p.characterId);
   if(portalOverlay || p.characterId==620 || p.depth==20) main.removeTag(t);
  }
  main.setModified(true);s.saveTo(new FileOutputStream(args[1]));
 }
}
