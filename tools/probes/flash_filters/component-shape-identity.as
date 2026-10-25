stop();var seq=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
_root.onEnterFrame=function(){
 delete _root.onEnterFrame;
 var mc=_root.attachMovie("case0","source",1);mc.gotoAndStop(1);
 var child=mc.getInstanceAtDepth(29-16384);
 if(child==undefined){emit("error","missing wrapper");fscommand("quit");return;}
 var shape=child.getInstanceAtDepth(1-16384);var absent=child.getInstanceAtDepth(2-16384);
 emit("identity",[shape==undefined,shape===child,shape===mc,absent==undefined].join(","));
 emit("paths",[mc._target,child._target,shape._target].join(","));
 emit("depths",[mc.getDepth(),child.getDepth(),shape.getDepth()].join(","));
 var cm=child.transform.matrix;var sm=shape.transform.matrix;
 emit("matrices",[cm.a,cm.d,cm.tx,cm.ty,sm.a,sm.d,sm.tx,sm.ty].join(","));
 var control=child.createEmptyMovieClip("control",123);var lookup=child.getInstanceAtDepth(123);
 emit("control",[lookup===control,lookup===child,lookup._target,lookup.getDepth()].join(","));
 emit("done","ok");fscommand("quit");
};
