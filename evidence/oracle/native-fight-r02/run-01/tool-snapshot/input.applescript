on run argv
    set targetPID to (item 1 of argv) as integer
    set movieTitle to item 2 of argv
    set inputKey to item 3 of argv
    set holdSeconds to (item 4 of argv) as real
    tell application "System Events"
        set candidates to application processes whose unix id is targetPID
        if (count of candidates) is not 1 then error "Ambiguous or absent PID"
        tell item 1 of candidates
            set frontmost to true
            delay 0.2
            if frontmost is not true then error "Target focus mismatch"
            if inputKey is not "escape" then
                if (count of windows) is not 1 then error "Ambiguous AX window"
                if name of window 1 is not movieTitle then error "Movie title mismatch"
            end if
            if inputKey is "escape" then
                key code 53
            else if inputKey is "s" or inputKey is "j" then
                try
                    key down inputKey
                    delay holdSeconds
                on error errorMessage number errorNumber
                    key up inputKey
                    error errorMessage number errorNumber
                end try
                key up inputKey
            else
                error "Input not in pinned menu vocabulary"
            end if
            return {unix id, frontmost, name of every window}
        end tell
    end tell
end run
