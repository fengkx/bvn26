# Byakuya boundary evidence r03

This directory retains ten additional base-form same-input comparisons for source id `白哉`, form frame `1`. The cases use explicit `魂/魂` helpers and the frozen runtime/generated artifact hashes in `manifest.json`.

Covered cases are four `690` 超必杀 cases (`mirror`, `wall`, `guard`, `energy_exact`), four `814` 招换 cases (`mirror`, `wall`, `air_target`, `guard`), `333` 招1 `wall`, and `455` 空中必杀 `mirror`. Each comparison has 602 parsed source fighter states and 602 Godot states across the 14 fields listed in its `comparison.json`; all ten matched with zero differences. This is focused state parity. It does not establish pixel parity, full AI parity, transformation parity, or parity for the remaining Godot-only fixtures. 万解 remains disabled.

The original-player capture was serialized with `/tmp/bvn-native-flash-capture.lock` and a 180-second lock timeout. The clean dynamic build had no frame-order or schedule intervention. The commands below describe a fresh rebuild from repository inputs; the checked-in evidence remains authoritative and no temporary directory is required to interpret it.

```sh
python3 tools/probes/build_ai_reference.py --ffdec /private/tmp/ffdec-26.2.1/ffdec-cli.jar --output /tmp/byakuya-matrix-boundary-r02 --run-id byakuya_matrix_boundary_r02 --frames 300 --dynamic-move-case --move-case evidence/characters/byakuya/fixtures-full/byakuya-454-bisha-neutral.json --p1-character 白哉 --p2-character 一护 --p1-helper 魂 --p2-helper 魂
mkdir -p /tmp/byakuya-matrix-cases-r03
for id in byakuya-690-bishaSuper-mirror byakuya-690-bishaSuper-wall byakuya-690-bishaSuper-guard byakuya-690-bishaSuper-energy_exact byakuya-814-zhaoHuan-mirror byakuya-814-zhaoHuan-wall byakuya-814-zhaoHuan-air_target byakuya-814-zhaoHuan-guard byakuya-333-magichit1-wall byakuya-455-bishaAir-mirror; do cp evidence/characters/byakuya/fixtures-full/$id.json /tmp/byakuya-matrix-cases-r03/$id.json; done
cat >/tmp/capture-native-180.py <<'PY'
import subprocess, sys
subprocess.run([sys.executable, "tools/probes/capture_native_player.py", "--lock-timeout", "180", *sys.argv[1:]], check=True)
PY
python3 tools/test_move_references.py --probe /tmp/byakuya-matrix-boundary-r02 --cases /tmp/byakuya-matrix-cases-r03 --native /tmp/byakuya-matrix-native-empty-r03 --output /tmp/byakuya-matrix-capture-r03 --capture-runner /tmp/capture-native-180.py --capture-only --allow-window-activation
python3 tools/test_move_cases.py --godot /private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --cases /tmp/byakuya-matrix-cases-r03 --output /tmp/byakuya-matrix-godot-r03 --jobs 1
```

The repository fixture directory contains a catalog manifest in addition to case files; the temporary directory must contain only the ten selected JSON cases. The runner writes the complete raw source trace, fixture, source build metadata, Godot states, and comparison under each case directory. `fixture-inventory-r03.json` is the all-178 fixture audit: 25 source-matched, 142 Godot-only, 11 disabled-negative, 0 invalid. The 25 are five pre-existing exact fixtures plus ten r02 and ten r03 boundary fixtures. The earlier report of 19 matched labels is label coverage, not 19 identical matrix fixtures; it does not imply that the 25 fixture count should equal 19. Disabled-negative means only the Godot matrix proves the action remains closed; it is not an original-player parity result.
