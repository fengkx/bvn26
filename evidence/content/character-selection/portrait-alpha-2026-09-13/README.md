# Character selection portrait alpha

The black rectangle came from the portrait conversion path, not the Godot draw call. In locked `game/main.swf` (SHA-256 `707fac0ec6bb2af1a3d18dc308dd403cb556a0988144b0f6f10555382287f92d`), Naruto's selection timeline is Sprite1346 frame 20. Shape1305 fills from JPEG3 bitmap1304; its exported RGB and alpha sidecar are `1304.jpg` and `1304.alpha.png`. Sprite1347 applies Shape591 as a clipping mask, and Sprite1348 applies RGB tint without changing alpha.

The portrait builder freezes Sprite1346 through XML and rebuilds a temporary SWF. JPEXS 26.2.1 turns the external JPEG3 definition into JPEG2 during this round-trip, dropping the sidecar alpha. The raster then contains a fully opaque 137×200 rectangle where the character bitmap was placed. Direct export from the untouched SWF retains the original transparency. Re-importing the source RGB plus alpha as one RGBA PNG under the same character ID restores the silhouette and soft alpha edge before Sprite1348 is rasterized.

For Naruto frame 1, the old round-trip PNG had 111,800 transparent, 0 partial-alpha, and 27,400 opaque pixels. Its entire `x=124..260, y=54..253` box was opaque; `(125,60)` was `(128,128,128,255)`. The regenerated frame has 123,188 transparent, 2,247 partial-alpha, and 13,765 opaque pixels; `(125,60)` is transparent. Opaque dark colors inside the character remain intact. The before screenshot and old red PNG are saved as `web-before.png` and `naruto-roundtrip-red.png` in this directory.

The converter now validates each RGB and alpha file against `export-report.json`, combines the original JPEG RGB with the alpha PNG's alpha channel, and uses FFDec `-importImages` before exporting the portrait frames. It does not infer transparency from RGB values. The source label frames and generated frame-1 hashes are:

Source asset hashes from the FFDec export report are `1304.jpg` = `d350586635cbd7f2e45945af90587f71c42db9db2803e969d340302240c15723` and `1304.alpha.png` = `379142753109fc35e9037aeb3129f42dec4c30466a5c59808ec2f78cefbabfd6`. The alpha-fix converter at that point was `ce46c520e6178e6928cff0c014a6a2b90eef201fbb36fa606f6c3ffd4e5f8855`; `MergeJpeg3Alpha.java` is `8798d6892fb4ba3d6bba7b783df0d08b8d631f2ebfd1006caa5be1bd9b943298`.

| Index | Selection label | Source frame | Frame-1 alpha counts (0 / partial / 255) | Frame-1 SHA-256 |
|---:|---|---:|---:|---|
| 0 | 鸣人 | 20 | 123188 / 2247 / 13765 | `1b7129f9e26b1a725a18bcb2fe2c5c42ceaf06bc804ca043c457967be6e37cbd` |
| 1 | 一护 | 1 | 71897 / 2830 / 15057 | `011644460d713ee29dc9d4579d3d2938ac8dea59922665fe447296b789227d87` |
| 2 | 日番谷 | 7 | 80370 / 1966 / 10464 | `725a2a490a9ec14c71384352759a0592fae10903c45c17132e171bc6bc7fff2a` |
| 3 | 恋次 | 6 | 73020 / 3791 / 15989 | `9d629d94e05858c7487633082882916b57ae8d6fd65b57803482eb9916005a90` |
| 4 | 佐助 | 24 | 127842 / 866 / 10492 | `aaba80b29f4db99350ebd40bf564ea739722a6b2ae1281593c464a7af11ec48a` |
| 5 | 卡卡西 | 27 | 122316 / 1192 / 15692 | `959f43de2134e56cec99a301931f83881f46fd7a363433c5f8efdd27637caec0` |
| 6 | 樱 | 23 | 126718 / 904 / 11578 | `72ea1cc532b4ab9751dc0163a5ce690daad68820c24e89d7b8eb1725386411a5` |
| 7 | 露其雅 | 4 | 74887 / 3156 / 11741 | `6d85ef11e4f75a451d12809909508fae855a72ff8733aee7c84e72319a1ae1d4` |
| 8 | 石田 | 12 | 125971 / 907 / 12322 | `556d9d2c38e034cb0f7aa318addc7f238fa2830ee066274aa51cadfa425fa18d` |

All 45 portrait frames were regenerated. `footer.json` contains the nine portrait names plus 魂、我爱罗、鼬 and 松本（catalog display name：松本·井野）. The QA page at [http://127.0.0.1:8765/sakura-roster-qa/index.html](http://127.0.0.1:8765/sakura-roster-qa/index.html) was re-exported with the fixed Naruto and 一护 assets; root verified both black rectangles were gone, the textured background showed through, clothing dark pixels remained, and the browser console had no errors or warnings.

After the full nine-person resource set was copied into the isolated QA project, its selector was restored to Sakura vs. Ichigo. Root refreshed the Web build in IAB and verified Sakura's large portrait and `春野·樱` footer, plus Ichigo's silhouette over the stage background; the dark clothing remains opaque and the console has no errors or warnings. Full QA PCK SHA-256: `0bc8d0f6c1c970c46ae929fb62a74d3970a8ad159a911d6bfd783ff5163da7b0`. This is an IAB visual check; Safari was unavailable and is not claimed as tested. Production selection availability was not opened by this QA change.

Validation:

- `python3 -m unittest tools.tests.test_selection_portrait_alpha` — 3 tests passed.
- `python3 -m unittest tools.tests.test_selection_registry.SelectionRegistryTests.test_new_roster_entries_have_source_baked_portrait_and_footer_names` — passed.
- `python3 tools/check_handoff.py` — passed.
- `python3 tools/verify.py` was run during shared integration and reports nine approved AI/compiler/runtime source hash changes; their hash manifest update is being integrated separately.

## High-resolution and Web canvas follow-up

The 1× table above records the alpha-fix baseline. It was visibly soft because FFDec rasterized the original selection bitmap at its small logical placement size before Godot enlarged the full game canvas. The locked source JPEG is 237×564 pixels; the bitmap-to-Shape and nested Sprite1347/1348 transforms reduce it to the portrait's logical bounds. FFDec `-zoom 2` rasterizes at twice the SWF logical bounds, rounding fractional dimensions up to whole pixels (e.g. Naruto 319.5×434.5 becomes 639×869; Ichigo 231.95×386.35 becomes 464×773). The renderer divides texture dimensions by `raster_scale=2` and retains the original five-logical-pixel raster border, so placement and portrait scale stay aligned with the source while the original bitmap is sampled at higher resolution. No AI upscaling, sharpening, or RGB-derived alpha was used.

The Web shell also forced CSS `width/height:100%` over a 900×600 backing canvas. In the measured browser session the CSS canvas was 630.734×420.484 CSS pixels at DPR 2, requiring 1261×841 physical pixels. This enlarged the entire scene, including UI text and background, with browser filtering. The shell now sizes the canvas CSS box to `#viewport` and its backing buffer to the measured box times DPR through `ResizeObserver`, window-resize, and fullscreen-change handling; the export preset uses the fixed logical canvas policy so the engine does not substitute window dimensions. The game keeps its 600×400 logical layout and 3:2 viewport.

Root's same-tab A/B at 1280×720/DPR2 measured 795×530 CSS pixels and 1590×1060 backing pixels in both r02 and r03. With canvas metrics held constant, r03's Sakura face/hair and Ichigo face/clothing edges were visibly sharper, while portrait positions and silhouettes stayed the same and the alpha cutout remained intact. Fullscreen and input validation are still pending and are not claimed here.

All 45 frames were regenerated at raster scale 2 and `portraits.json` now records that scale for each character. The new frame-1 outputs are:

| Source frame | Character | Raster size | Alpha counts (0 / partial / 255) | SHA-256 |
|---:|---|---:|---:|---|
| 20 | 鸣人 | 639×869 | 491125 / 9021 / 55145 | `1f330d2dd785ac7c78d3068d0a9db778ac6de1251ec9d3952b67f8f9ad3d8746` |
| 1 | 一护 | 464×773 | 287110 / 11375 / 60187 | `9fbc68df9b1cc33cc4f886d3145592e6f4a9b7d0bb8646620f1f4096b6631452` |
| 7 | 日番谷 | 464×799 | 320705 / 7948 / 42083 | `b29ebfce2d7d1223ea732d7dc1b74b28ccaa5a0d664fc5096fe001ccb2120bb6` |
| 6 | 恋次 | 464×799 | 291487 / 14899 / 64350 | `26162cfa0cd479067d527be6d1063157c0f393068cf4902d799310861f1d3b47` |
| 24 | 佐助 | 639×869 | 509647 / 3483 / 42161 | `daa5bad22c89d1aa0389447228654840cbaa500ee634b8a3b174b895186bb91c` |
| 27 | 卡卡西 | 639×869 | 487543 / 4604 / 63144 | `aba04ee7e2e8fb82d24db1950e6cf57aadb1d7f615e3bd04531038abe945380a` |
| 23 | 樱 | 639×869 | 505206 / 3838 / 46247 | `e873fa4a94278cd80e572e3ddc6d94af5a24fa9658bafa211aa31e2de917e7eb` |
| 4 | 露其雅 | 464×773 | 298748 / 12846 / 47078 | `63ac5490414e8a49ee9e4c5c3904858410f1cab4c7a879f250098253335899b0` |
| 12 | 石田 | 639×869 | 502240 / 3586 / 49465 | `0215f2d9b0144a8b0b58e0f6171118e9bfab1631291526ece96b3dc878b55278` |

The updated QA export is at [http://127.0.0.1:8765/sakura-roster-qa/index.html](http://127.0.0.1:8765/sakura-roster-qa/index.html). Its PCK SHA-256 is `3862215b7b101db4401939b096e99491a78dda652a4d7043b7b3c1ad44b40e37`, independently confirmed in the final IAB check. At 671×781 CSS pixels and DPR 2, the canvas measured 1261×841 physical pixels and 630.734375×420.484375 CSS pixels. Sakura and Ichigo were visibly clear, retained their cutout alpha, and kept the expected position and proportions; the console had no errors or warnings. Fullscreen returned to window mode immediately, and a short `d` key attempt did not change the selection, so sustained fullscreen and gameplay input remain unverified.

Relevant implementation hashes: `shell.html` = `37e27729a897d5fda3a05cb059ae8adcc6343e7d09595d4897709e7fe98198b7`, `export_presets.cfg` = `e6c1e807f90872fc9f22fc8b9fa01cf8de21228f2ddead52dcc73fdcdbc835cf`, `character_selection.gd` = `0065d9a992924c6e3ee79d82f5aaa7ef4ddaf32ecd166a00543ad045445c1c7d`, and `build_selection_portraits.py` = `9eb515df1952b47cadbd00f03bdba83bf5b058d938c5dd2c6ecd47577bfa307c`.

Additional validation: `python3 -m unittest tools.tests.test_selection_portrait_alpha` — 4 tests passed, including all nine character metadata records and all 45 PNG dimensions against the exact SWF logical bounds.
