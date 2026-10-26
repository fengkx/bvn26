# Read-only debugger availability check

- `xcrun --find lldb` resolves `/Applications/Xcode.app/Contents/Developer/usr/bin/lldb`.
- Version is `lldb-2103.0.34.103`.
- LLDB `target create --arch x86_64` accepts the installed pinned Flash Player Debugger executable; static disassembly at `0x10029dad0` succeeds. See `lldb-static-target.log`.
- `codesign -d --entitlements :-` reports `com.apple.security.cs.debugger=true` along with JIT/library-validation entitlements; `com.apple.security.get-task-allow` is absent. See `player-entitlements.log`. This output alone does not establish whether a debugger may attach or launch under the current host policy.

No process launch, attach, breakpoint, expression execution, memory write, process injection, security-policy change or new native capture was performed by this check. Rosetta runtime register/operand capture remains **unverified**. A static LLDB target is not evidence of runtime debugger support, and no system configuration change is requested.
