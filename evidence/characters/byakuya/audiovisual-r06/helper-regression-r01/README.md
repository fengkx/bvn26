# Current helper FIFO regression

The existing strict same-input fixtures were executed with the current helper runtime:
`lee-34-jump-held` (source helper frame 84 observed) and
`byakuya-814-zhaoHuan-neutral` (source helper frame 101 observed in the retained
trajectory). Both used the persisted source fixture and existing raw capture;
no Flash capture was started.

Godot command:

```sh
python3 tools/test_move_cases.py --godot /private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --cases /tmp/byakuya-helper-regression-cases --output /tmp/byakuya-helper-regression-godot --jobs 1
```

The fighter state comparisons each contain 602/602 rows over the strict 14
fields. The helper comparisons contain 602/602 rows over frame, position,
orientation, action and attacking. Both are validated with no differences.
The raw helper snapshots are retained beside normalized comparator inputs.
