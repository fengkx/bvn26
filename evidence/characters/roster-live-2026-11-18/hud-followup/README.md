# Itachi HUD follow-up

The same original input was replayed to tick 175 with recorded Math.random and
hurtVoice clock inputs. The terminal capture allows four renderer frames to
settle; a second run renders every fight tick. Both still omit the top HUD.
This remains a visible difference from the original capture.

A separate diagnostic experiment raised only the HUD z_index from 110 to 2000;
it did not restore the HUD. This intervention is not an acceptance run or a
production fix. All production files remained unchanged by these probes.
