# Common project commands

# 列出可用命令
default:
  @just --list

# 校验交接与工具输入完整性
verify:
  python3 tools/verify.py
  python3 tools/check_handoff.py

# 按项目约定运行完整契约校验（自动创建并复用 .venv）
validate-contracts:
  if [ ! -d .venv ]; then \
    python3 -m venv .venv; \
    .venv/bin/python -m pip install -r requirements-dev.txt; \
  fi
  .venv/bin/python tools/validate_contracts.py

# 导出 Godot Web（兼容现有 build_web.sh 的行为）
export-web:
  ./tools/build_web.sh

# 清理 dist/web 后重新导出 Web
export-web-clean:
  rm -rf dist/web
  ./tools/build_web.sh

# 仅列出当前可复用的 Godot 测试文件（便于后续扩展 just 命令）
list-godot-tests:
  rg -n "SMOKE_OK|_smoke\\.gd$" godot/tests
