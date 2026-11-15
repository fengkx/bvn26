# Temari / 手鞠 — blocked source-bound candidate

Base: `a3b479414546250b7d0cd6e35cbc3ae52b3169d1`.
Branch: `port/shouju-base`.
Worktree: `/Users/fengkx/me/agent-code/bvn2_6-shouju`.

This is committed WIP, not a playable accepted port. No PR, merge or deployment.
The source selector, manifest catalog and coverage order confirm 手鞠 from
`game/fighter/shouju.swf` immediately after 小乌. See `selection-order.json`.
Standalone form variants remain deferred. No other character is started.

## Source and lifecycle

The locked SWF SHA-256 is
`71749a25bd0cab546e89a09c2aa37ca455a725e4c1fd4e388f63b6babe03eb5d`.
Root frame 1 places BODY 541. `source-first.json` inventories all 1,279 BODY
frames (including empty frames), scripts, placement/MOVE/removal changes,
sound events and wrapper scripts. No replacement BODY is activated by this work.

- Standing frame 2 clears hits. New controller placements initialize local
  fields; MOVE preserves instances. The existing compiler retains this distinction.
- Combo controller windows start at 226, 256 and 294. They retain authored
  predicate ordering, including cancellation to ranged attacks and supers.
- Normal super costs 100 at 600, starts presentation at 601, resumes at 617,
  and explicitly returns at 652. Upper super costs 100 at 688, starts at 689,
  resumes at 708, and returns at 741. Ultimate costs 300 at 790, starts at 792,
  resumes at 822, and returns at 934. All use the source face label 手鞠1.
- The normal-super controller placed at 618 calls moveX(30) when unpaused.
  Its lifetime comes from the timeline, not a guessed duration.
- Defence/hurt/flying callbacks are at 1035/1047/1060. Receiver rules are shared;
  no character-specific runtime patch was introduced.
- Source frame-call checks compare fresh strict compilation with the cache and
  reject deletion of every compiled call. The new requirements entry is pinned
  only to this SWF hash and BODY. No key or guard was disabled.

The fifth source-first question remains unanswered: fresh same-input original
Flash observation is blocked. Static source assertions do not settle observed
callback timing, repeat-cast behavior, rendering or audio parity.

## Build

Use Python 3.11+ (the system Python 3.9 attempt failed and is retained):

```sh
python3 tools/importer/export_swf_xml.py \
  --ffdec-jar /Users/fengkx/me/agent-code/toolchains/jpexs-26.2.1/ffdec-cli.jar \
  --output-dir /private/tmp/bvn-shouju-export game/fighter/shouju.swf
/opt/homebrew/bin/python3 evidence/characters/shouju/build_port.py \
  --workspace /private/tmp/bvn-shouju-export \
  --ffdec /Users/fengkx/me/agent-code/toolchains/jpexs-26.2.1/ffdec-cli.jar \
  --ffmpeg /opt/homebrew/bin/ffmpeg
```

Generated assets and controllers are an isolated candidate. Selection/catalog
activation is pending fresh original observations and native verification.
The source compiler accepts the package without shared runtime changes.

The UI font was actually regenerated from Sarasa UI SC collection index 199,
using `build_menu_font.py`; the non-ASCII coverage test ran and passed. The first
attempt failed on the default uv cache permission. The second used a writable
temporary dependency cache; it did not install or replace the restored toolchains.

## Blockers and acceptance scope

The desktop reports `CGSSessionScreenIsLocked=Yes`; `logs/desktop-state.log`
records the observation. No Flash process was launched by this task. Do not
unlock, steal another session's lock or use a foreground session. Any future
Flash launch must use the external lock with holder `bvn-temari-port`.

Fresh Flash/native targeted comparisons, continuous lifecycle observations,
saved-roster replay, headed rendering and Web checks remain pending. The prior
headed RID/resource leaks and saved-roster exit resources-in-use remain unaccepted;
this candidate does not fix or clear them. No complete 1:1 or production admission
is claimed. Six proof/admission flags remain false in `checks.json`.

The user supplied approximately 4% weekly quota at handoff. No current quota
meter is exposed through the available task tools, so that is not a live reading.
No hard quota-block response was observed and no extra quota was purchased.

Continue only this character: obtain fresh original evidence when the desktop is
available, complete native/catalog integration and targeted/saved-roster gates,
then open one Draft PR only if the requested SOP bar is met.
