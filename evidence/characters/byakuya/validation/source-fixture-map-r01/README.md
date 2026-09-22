# Byakuya source/fixture map r01

This is a read-only archive map for all 178 fixture IDs from `fixture-inventory-r03.json`. It records retained raw event path and SHA-256, source build path and SHA-256, fixture path and SHA-256, build case identity/status, and any existing comparison artifact. It does not execute Godot or infer source parity.

Counts: {'disabled-negative': 11, 'source-build-fixture-consistent': 161, 'no-retained-source-archive': 6}. `source-build-fixture-consistent` means a retained raw source archive, build metadata whose `move_case.id` equals the fixture ID, and a fixture hash matching the inventory. `disabled-negative` remains disabled by fixture policy. `no-retained-source-archive` means this workspace map found no retained raw/build/fixture triple; it is not a claim that an old `/tmp` capture never existed.

The known `byakuya-690-bishaSuper-hp1-ko-r01` initial-health mismatch remains separately invalid and is excluded from validated counts.
