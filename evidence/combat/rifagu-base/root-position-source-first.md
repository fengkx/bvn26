# Root position source gate

- Frame scripts: `scripts/fighter/rifagu.json`,
  `DefineSprite_638/frame_254/DoAction.as` subtracts 2 from `_root._y`;
  frames 255/256/257 add/subtract/add 2. Frames 428/429/430/431 repeat
  this sequence. Frame 964 assigns zero. The complete base frame inventory,
  including empty frames and secondary DoAction records, is in `source-audit.json`.
- Placement/lifetime: these are root frame scripts, not new per-frame callbacks.
  Hit effect frame scripts run on the existing shared callback registry.
  `DefineSprite_358_XG_ice` frame 2 has `_root._x = _root._y = 3`;
  frame 13 assigns both axes zero. `DefineSprite_176_XG_hitfloor` frames
  2 through 8 contain independent axis assignments and a chained reset.
- Exit: the fighter's `砍技1` exits at 280 through `gotoAndStop("站立"); play();`.
  Effects retain their original unload and pause/resume events. A root position
  write must not change fighter playback or cancel effect lifetime.
- Invariant: `=` replaces an axis, `+=`/`-=` accumulate, and chained assignment
  writes the inner axis first. Position applies to the entire root display,
  including HUD; it is not camera interpolation or fighter displacement.
- Original same-input capture: `/tmp/bvn-rifagu-presentation-events-r5`,
  fixture `rifagu-248-skill1-neutral`, P1 日番谷/P2 一护, 300 ticks, exact
  source key-read verification. Root Y is -2 at fight ticks 19 and 21;
  the ice effect produces (3, 5) at tick 22, followed by authored shake
  coordinates and reset. The landing effect produces (1, 5) at tick 58.
  The unmodified port leaves the root at (0, 0), so fighter-only matches
  do not establish presentation parity.

This gate covers root translation only. Other visual/audio fields require
their own comparison evidence; no full acceptance is asserted here.
