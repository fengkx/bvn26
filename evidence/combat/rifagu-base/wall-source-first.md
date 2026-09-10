# Wall contact and receive push: source-first gate

1. Per-frame scripts: `scripts/main.json#DefineSprite_1991/frame_1/DoAction.as`
   defines the scene enterFrame. After actors move, it clamps every gamePlayers
   wrapper to 20 .. mapSizeX - 30 and writes hitWall before distance locking and
   camera interpolation. Each fighter base frame-1 onBeHit checks that flag,
   sets hitNear when opponent distance is below 100, then checks the authored
   facing/500 split. beidax uses hitNear for the existing opponent push.
2. Placement/MOVE: base Sprite 638's outer frame-1 placement invokes BODY
   on_enterframe. Fresh outer-callback instrumentation shows P2 then P1 in both
   engines. P2 clamps itself, then P1 overlap pushes it beyond the right wall;
   the older scene callback clamps it again. No instance replacement is involved.
3. Leaving labels: these callbacks do not introduce a goto or alter any label
   exit. Existing beidax/timeline transitions remain compiled from source.
4. Invariants: observe the scene clamp before root sampling and deferred goto
   scripts; hitNear changes only in the original wall branch, including its
   strict distance/side comparisons. Do not change impulses, hitboxes or damage.
5. Same-input comparison: retained long-U originals under
   /tmp/bvn-rifagu-body-order-original-r1/rifagu-348-magichit1-held and
   /tmp/bvn-rifagu-root-writers-original-r1/rifagu-348-magichit1-held agree.
   At observation 99 P1/P2 X are 965/966; at 100 Flash is 960/970 while the old
   port is 960/975. Moving the existing scene callback corrects the first
   difference; the next difference at 116 exposes the omitted hitNear write.
   Post-fix long-U matches all 602 actor rows and 301 root rows exactly.
   Existing PvP and training-timer originals also match all 1,204 actor rows.
   Compressed originals, old failures and current results are in wall-contact/.

The wall branch is compiled into each base combat model and interpreted by the
shared receiver. Bankai acceptance is outside this task's current scope.
