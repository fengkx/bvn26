# Helper FIFO review r01

只读审查当前 helper initial-frame FIFO 变更，未修改 runtime。

已确认：generation guard 会拒绝 stale callback；main 使用 `source_frame_sequence` 将 child callback 与 fighter pending frame 排序；nested goto 通过同一 FIFO 保留顺序。

待证风险：`godot/helper_runtime.gd:296-301` 的 `_events_applied` 只按 frame 去重，因此同一 activation 内 A→B→A 可能跳过第二次 A frame script；在没有 source 证据前不能宣称一般 re-entry 支持。另，`source_child_frame_requested` 只要存在任意连接就走 deferred 分支，独立 probe 要明确这是 production FIFO 模式还是 standalone fallback。
