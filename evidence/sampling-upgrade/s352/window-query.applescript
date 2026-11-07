tell application "System Events"
    set targets to application processes whose name is "Flash Player"
    set report to "matching_processes=" & (count of targets) & linefeed
    repeat with target in targets
        set report to report & "pid=" & (unix id of target) & ";frontmost=" & (frontmost of target) & linefeed
        repeat with targetWindow in windows of target
            set report to report & "window=" & (name of targetWindow) & linefeed
        end repeat
    end repeat
    return report
end tell
