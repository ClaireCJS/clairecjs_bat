className := A_Args[1]
x := A_Args[2] * 1
y := A_Args[3] * 1
;width := A_Args[4] * 14
;height := A_Args[5] * 1

try {
    WinList := WinGetList("ahk_class " . className)
    for index, hwnd in WinList {
        ; To debug, let's print the title of each window we found
        ;MsgBox "Found window with title: " . WinGetTitle("ahk_id " . hwnd)
        try {
            ;WinMove("ahk_id " . hwnd, "", x, y, width, height)
	    WinMove("ahk_id " . hwnd, "", x, y)
	    ;WinMove(hwnd, "", x, y)
        } catch {
            MsgBox "Failed to move window with hwnd: " . hwnd
        }
    }
} catch {
    MsgBox "No windows found with class name: " . className
}
