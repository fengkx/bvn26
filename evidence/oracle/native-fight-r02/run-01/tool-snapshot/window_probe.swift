import AppKit
import CoreGraphics
import ApplicationServices
let apps = NSWorkspace.shared.runningApplications.filter { $0.bundleIdentifier == "com.macromedia.Flash Player Debugger.app" }
let cg = CGWindowListCopyWindowInfo(.optionAll, kCGNullWindowID) as? [[String: Any]] ?? []
var rows: [[String: Any]] = []
for app in apps {
 let ax = AXUIElementCreateApplication(app.processIdentifier)
 AXUIElementSetMessagingTimeout(ax, 3)
 var value: CFTypeRef?
 let error = AXUIElementCopyAttributeValue(ax, kAXWindowsAttribute as CFString, &value)
 let windows = value as? [AXUIElement] ?? []
 var titles: [[String:Any]] = []
 for window in windows {
  var title: CFTypeRef?
  let e = AXUIElementCopyAttributeValue(window, kAXTitleAttribute as CFString, &title)
  titles.append(["title_error": e.rawValue, "title": title as? String ?? ""])
 }
 rows.append(["pid":Int(app.processIdentifier),"executable":app.executableURL?.path ?? "", "bundle":app.bundleURL?.path ?? "", "ax_windows_error":error.rawValue, "ax_windows":titles,"cg_windows":cg.filter { ($0[kCGWindowOwnerPID as String] as? Int) == Int(app.processIdentifier) }])
}
let result: [String:Any] = ["accessibility_trusted":AXIsProcessTrusted(),"screen_capture_preflight":CGPreflightScreenCaptureAccess(),"frontmost_pid":Int(NSWorkspace.shared.frontmostApplication?.processIdentifier ?? -1),"applications":rows]
let data = try JSONSerialization.data(withJSONObject: result, options:[.prettyPrinted,.sortedKeys])
print(String(data:data,encoding:.utf8)!)
