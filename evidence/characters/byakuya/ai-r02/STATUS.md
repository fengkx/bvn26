# Invalid fixture status

`ai-r02` used `frame_order_probe=true`. That probe injects the source fixture
sequence `p2 goto389, action1, rootpause`; its behavior and frame comparisons are
invalid for AI acceptance. The random ordering and sensor diagnostics remain
useful research artifacts only.

Use `evidence/characters/byakuya/ai-clean-r01` for the clean Vs-Com capture.
