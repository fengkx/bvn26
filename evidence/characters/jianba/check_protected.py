"""Verify the explicitly retained PR #37 function without normalizing bytes."""
import hashlib
import re
from pathlib import Path

source = Path('godot/fighter_runtime.gd').read_bytes()
function = re.search(rb'func _clear_interrupted_super_preparation\(.*?(?=\nfunc )', source, re.S)[0]
assert len(function) == 1086
assert hashlib.sha256(function).hexdigest() == '9da62022432d7093b22b265b9e411db392ede4cbb1656fec21fe244f93f274ed'
print('PROTECTED_FUNCTION_OK bytes=1086 sha256=9da62022432d7093b22b265b9e411db392ede4cbb1656fec21fe244f93f274ed')
