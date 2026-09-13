# Jinye owner-hit and reactivation case

Run ID: `moves-sakura-jinye-owner-hit-natural-end-reactivate-r01`.

The fixture summons Jinye, has the opponent hit Sakura while the helper is active, then summons Jinye again after its source clip finishes. The retained Flash capture contains 9,974 events and a complete 300-frame post-ready run. At fight tick 24 Sakura is hit (source frame 891, HP 960, hit count 1) while Jinye is still active at frame 10. Jinye reaches source frame 73 at tick 87 and parks at frame 1 at tick 88. The second helper spawn is recorded at tick 130 and Jinye is active at frame 2 at tick 131.

Both `comparison/helper-owner-hit-r01-fighter.json` and `comparison/helper-owner-hit-r01-helper.json` report exact 602/602 matches. The helper comparison covers frame, position, orientation, action, and attacking state; source-only hit-box fields are not claimed as compared in this case. Runtime snapshot hashes used for replay: `fighter_runtime.gd` `1e42dbdda58bfbe5ad88c0d5c5d89a7d6471ea266086b8a228cf2f53737b4f38`, `helper_runtime.gd` `25563ef23758f9b1b0ba5a6042d8508feef75841e961aa40aea86b806a61c4b0`, `timeline_preview.gd` `b027e478c56b5cb234ec617744a24fc1b0f7bd69a2311c482211beb0ba890f7f`, `ai_source_state.gd` `f11f47d9c1cc5c8676119a0c9f7a1b77a235b4c41ccf1a24eedc0da0ae7cb544`, and `ai_controller_host.gd` `5123a79d3232ca32a6cb917724a32d8d6bae5bae21bce538c4727ca21d069f17`.

The original build explicitly selected p1 helper 松本/Jinye and p2 helper 魂/Kon. The source capture and native replay use the same fixture inputs. Source audit found no `removeFZ` call site for this path, so the evidence supports natural completion and reactivation; it does not support immediate helper cleanup on owner hit.
