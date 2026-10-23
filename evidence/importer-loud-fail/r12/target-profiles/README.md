# r12 isolated replacement profiles and complete dependency blockers

These packages remain **runtime_integrated=false**. No target assets from this
track were published under production generated fighters. A successful package
build or script parse is not replacement/native/rollback acceptance.

Three complete parent-frame-2 candidate packages built in scratch, with source
visual/combat/controller/BODY/sound products:

| Original source | Target body | Candidate directory | Files |
|---|---:|---|---:|
| Sasuke.swf | 1019 | /tmp/bvn-loud-fail/r12/sasuke-profile | 299 |
| minren.swf | 1293 | /tmp/bvn-loud-fail/r12/minren-profile-v2 | 329 |
| yihu.swf | 1180 | /tmp/bvn-loud-fail/r12/yihu-profile-v2 | 313 |

`candidate-builds.json` pins each package tree hash, source hash, bytes and status;
`*-files.json` contains exact file hashes without committing the packages.
`compiler-hashes.json` pins the compiler snapshots. Programs were refreshed after
the source initialization metadata and player hurt-hook compiler were added.
All 12 CPU/player controller/BODY scripts pass Godot --check-only (profile-parse.json).
The scalar callback regression and native evidence are in ../missing-fields/.

Sasuke's target has no further parent-goto/wankai call outside frame 1 in its
locked bundle. It still lacks full production replacement native/Godot/rollback
acceptance and persistent p1bs/p2bs ownership evidence; it is not enabled.

## Required third forms are not omitted

- **Minren:** base 764 -> parent 2/body 1293 -> original
  `DefineSprite_1293/frame_1157/DoAction.as` `_parent.gotoAndStop(3)` -> body 1821.
  Extracting parent 3 fails at `game/fighter/minren.swf/root/frame_3/depth_1`:
  wrapper GlowFilter 7x10, passes 3, remains unsupported. The strict wrapper-field
  guard rejects it; the parent 2 package cannot be installed as a complete graph.
- **Yihu:** base 638 -> parent 2/body 1180 -> original
  `DefineSprite_1180/frame_1036/DoAction.as` `wankai()` -> parent 3/body 1672.
  That target has two independent hard failures: combat compilation reports
  `Expected one energy cost for 必杀, got 0` (the label begins at source 537);
  CPU/player controller compilation rejects
  `DefineSprite_1672/frame_390/PlaceObject2_16_34/CLIPACTIONRECORD onClipEvent(enterFrame).as`
  `_parent._parent._xscale *= -1;`. The parent 3 candidate build confirms the latter
  failure under candidate mode (yihu-parent3-profile.log). Parent2 alone is not a
  complete graph. Neither terminal body 1821 nor 1672 has another non-frame 1 parent
  goto/wankai call in its locked bundle; this bounded scan does not complete the
  broader AS audit.

`follow-on-requirements.json` includes all four parent 2/parent 3 requirements and
source/load hashes. `follow-on-staging.json` preserves the separate stage results.
The staging tool intentionally uses the ordinary compiler mode, so its parent 2
errors predate the candidate-specific compile path. They are resolved in the
three candidate builds above; its parent 3 placement/combat/controller errors
remain current. No failure was allowlisted or stripped.

## Reproduction

Use a fresh staging/package directory, the pinned JPEXS 26.2.1, and ffmpeg:

```sh
export JAVA_TOOL_OPTIONS="-Duser.home=$SCRATCH/java-home"
python3 tools/importer/stage_parent_forms.py \
  --requirements evidence/importer-loud-fail/r12/target-profiles/sasuke-requirements.json \
  --ffdec "$FFDEC" --output "$SCRATCH/staged-sasuke"
python3 tools/importer/build_form_profile.py \
  --staged "$SCRATCH/staged-sasuke/Sasuke-2" --base godot/generated/fighters/sasuke \
  --output "$SCRATCH/sasuke-profile" --ffdec "$FFDEC" --ffmpeg "$FFMPEG"
python3 tools/importer/stage_parent_forms.py \
  --requirements evidence/importer-loud-fail/r12/target-profiles/follow-on-requirements.json \
  --ffdec "$FFDEC" --output "$SCRATCH/staged-follow-on"
```

Staging exits 1 for the recorded strict errors while retaining independent
products. Build minren-2/yihu-2 using their corresponding base directories and
fresh output directories; all candidate flags are set by build_form_profile.py.
Do not bypass the minren-3 wrapper failure or treat yihu-3's missing combat model
as an optional asset. The actual build logs and full required graph remain here.
