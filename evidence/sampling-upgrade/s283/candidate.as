function on_enterframe()
{
   initWudi();
   if(ql < 0)
   {
      ql = 0;
   }
   if(ql > 300)
   {
      ql = 300;
   }
   if(hp < 0)
   {
      hp = 0;
   }
   if(_parent._x < 20)
   {
      _parent._x = 20;
   }
   if(_parent._x > _root.mapSizeX - 30)
   {
      _parent._x = _root.mapSizeX - 30;
   }
   if(_root.s283Value("dashing", dashing, this))
   {
      onDashing();
      if(_parent._y > _root.floorY)
      {
         _parent._y = _root.floorY;
      }
      _lastX = _parent._x;
      return undefined;
   }
   if(_root.s283Value("paused", _root.zhanting, this))
   {
      return undefined;
   }
   if(wdFrameX > 0 && !isNaN(wdFrameX) && !isNaN(wdFrame))
   {
      canhit = false;
      if(++wdFrame >= wdFrameX)
      {
         canhit = true;
         wdFrame = wdFrameX = 0;
      }
   }
   if(!dashing)
   {
      doDashX();
   }
   var _loc6_ = _root.game["p" + pn];
   var _loc4_ = _parent._x - _lastX;
   if(_loc4_ > 30)
   {
      _loc4_ = 30;
   }
   if(_loc4_ < -30)
   {
      _loc4_ = -30;
   }
   var _loc3_ = _loc4_ * _parent.scale_X;
   if(_loc3_ > 0)
   {
      _loc3_ += _loc6_.vecx / 2;
      _parent.vecx = _loc3_;
   }
   else
   {
      _parent.vecx = 0;
   }
   var _loc8_;
   var _loc5_;
   var _loc11_;
   if(_root.s283Value("own_air", airBody == false, this) && _root.s283Value("other_air", _root.game["p" + pn].mc.airBody == false, this))
   {
      if(_root.s283Value("displacement", _loc3_ >= 0, this) && _root.s283Value("result", _root.s283Value("receiver", bdmn, this).hitTest(_root.s283Value("target", _root.game["p" + pn].mc.bdmn, this)), this))
      {
         if(_loc3_ == 0 && _loc6_.vecx == 0)
         {
            _loc3_ = 10;
         }
         _loc8_ = _loc6_.heavy - _parent.heavy;
         if(_loc8_ < 0)
         {
            _loc8_ = 0;
         }
         _loc5_ = _loc3_ / 2 - _loc8_;
         if(_loc5_ < 0)
         {
            _loc5_ = 0;
         }
         _loc11_ = _loc3_ - _loc5_;
         _loc6_._x += _loc5_ * _parent.scale_X;
         _parent.moveX(- _loc11_);
      }
   }
   _lastX = _parent._x;
   var _loc10_ = true;
   var _loc7_ = _parent._y;
   if(_loc7_ == _root.floorY)
   {
      touch = true;
      touchFloor = true;
      return undefined;
   }
   var _loc9_;
   if(_loc7_ < _root.floorY)
   {
      _loc9_ = isHitBan();
      hitBan = _loc9_ != 0;
      if(jump == 1)
      {
         touch = false;
         touchFloor = false;
         return undefined;
      }
      if(hitBan)
      {
         touch = true;
         touchFloor = false;
         _parent._y = _loc9_;
         return undefined;
      }
   }
   if(_loc7_ > _root.floorY - 10)
   {
      _parent._y = _root.floorY;
      touch = true;
      touchFloor = true;
      return undefined;
   }
   if(_loc10_)
   {
      touch = false;
      _parent._y += _root.zhongli;
      if(jumped == 1)
      {
         gotoAndStop("落");
         play();
         jumped = 0;
      }
      if(jumped == 2)
      {
         gotoAndStop("落2");
         play();
         jumped = 0;
      }
   }
}
