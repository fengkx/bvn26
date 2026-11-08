import AppKit
import CoreGraphics
import ApplicationServices

let bundleID = "com.macromedia.Flash Player Debugger.app"
let apps = NSWorkspace.shared.runningApplications.filter { $0.bundleIdentifier == bundleID }
let pids = Set(apps.map { Int($0.processIdentifier) })
let windows = CGWindowListCopyWindowInfo(.optionAll, kCGNullWindowID) as? [[String: Any]]
let selected = windows?.filter { pids.contains(($0[kCGWindowOwnerPID as String] as? Int) ?? -1) }
let result: [String: Any] = [
    "applications": apps.map { app -> [String: Any] in
        ["pid": Int(app.processIdentifier), "bundle_url": app.bundleURL?.path ?? "",
         "executable_url": app.executableURL?.path ?? "", "active": app.isActive,
         "hidden": app.isHidden, "terminated": app.isTerminated,
         "launch_date": app.launchDate?.description ?? ""]
    },
    "window_query_available": windows != nil,
    "player_windows": selected ?? [],
    "accessibility_trusted": AXIsProcessTrusted(),
    "screen_capture_preflight": CGPreflightScreenCaptureAccess()
]
let data = try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys])
print(String(data: data, encoding: .utf8)!)
