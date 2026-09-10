# Repeated Hitsugaya down + I ice placement

The first cast was correct, but the per-frame placement deduplication survived
subsequent source action entries. New cbs1atm instances reset to their authored
(136.5, -10.5) local placement while frame 670's assignment was wrongly skipped.
The repeated-cast regression reproduces that exact default on its second cast.

## Source-first gate

- `scripts/fighter/rifagu.json`, DefineSprite638: frame 620 sets action/bs, spends 300 energy and sets jump; 622 calls cbsd/showFace; 665 calls cbsw; 666 places the beida callback; 670 assigns cbs1atm X relative to opponent with facing compensation and Y as opponent Y minus parent Y, then shines; 671 shines; 760 sets action 0; 800 goes to standing and plays. Remaining root frames in this action have no DoAction. The full inventory is retained in `../source-audit.json`.
- At frame 670 cbs1atm is a new Sprite490 at depth 28, with matrix translation (2730, -210) twips. Following MOVE/retained frames keep that instance. Sprite490 frame 85 renames itself cbsatm, and 89 shines. The positioning assignment is unconditional each time root frame 670 executes.
- The action exits through the explicit frame-800 gotoAndStop(standing)/play. No label-end or lifetime rule changes.
- Invariant: every new cast must execute the opponent-relative assignment again. Retained frame 671 must keep the value and must not continuously chase a moving defender. Tests exercise three casts on the same actor instances, both facings and different distances. Controlled test setup enters the source action and supplies energy; it is not a fresh-fight-per-cast test.
- The 11 retained original down+I fixtures still match all 6,622 actor observations (`comparisons.json`); those are single-cast or short held-input observations. The new repeated-cast source-assignment/native/Web regression is separate, and no new repeated original-player full-match capture is claimed.

## Repair and checks

Reset only placement-event bookkeeping in the shared source action-entry path,
alongside other source event bookkeeping. Live clip offsets still follow their
PlaceObject lifetime; the change does not clear them at adjacent labels.
No coordinates, collider sizes, lock-on behavior or character-specific rule
is added.

- Before: first cast local (400,0), second cast incorrectly (136.5,-10.5), exit 1.
- After: casts resolve to (400,0), (600,0), (350,0), with retained-placement checks passing.
- Native screenshot `second-cast-mirrored.png`: attacker right, ice on the left-side defender.
- 93 Python tests pass; all 11 retained down+I source comparisons remain matched.

- Chromium WebGL repeats all three placements with the same expected coordinates and passes the retained-frame assertion (`web-log.json`).
- Source integrity, handoff and contract checks pass. The production Web build is updated locally; deployment was not performed.
