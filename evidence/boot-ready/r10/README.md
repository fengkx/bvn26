# Native boot/menu probe r10

This is a failed, source-preserving UI-driver attempt. The probe was built with run ID `boot-ready-r10-20260921` and the original Flash capture contract. The window was moved to `{120,120}` through System Events and captured by window ID `129977`; the title/menu screenshot shows the original main menu with `Normal` selected and status text `普通单人模式`.

The source menu actions are `DefineSprite_594/frame_15/DoAction.as` (Normal, modo 1), `DefineSprite_597/frame_15/DoAction.as` (Vs COM, modo 2), `DefineSprite_600/frame_15/DoAction.as` (Vs Human, modo 3), and `DefineSprite_603/frame_15/DoAction.as` (training, modo 4). The attempts were: Enter, System Events `keystroke "j"`, AX click, CGEvent click, and CGEvent macOS virtual key 38 held for 300 ms. None produced a selection transition. The final key attempt caused the Flash window to disappear; the capture ended with `events=2, done=false`, and `original.log` contains only `root_frame_1` and `root_frame_10`.

This artifact does not establish menu input acceptance or Ready. The likely remaining tool boundary is Flash canvas focus/input delivery; no runtime or source input code was changed.
