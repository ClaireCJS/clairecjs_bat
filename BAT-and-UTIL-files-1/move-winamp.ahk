
try {
    WinMove("ahk_class Winamp v1.x","",100,100)
} catch {
    MsgBox "Failed to move winamp"
}


;try {
;    WinList := WinGetList("ahk_class " . className)
;    for index, hwnd in WinList {
;        ; To debug, let's print the title of each window we found
;        try {
;            ;WinMove("ahk_id " . hwnd, "", x, y, width, height)
;	    WinMove("ahk_id " . hwnd, "", x, y)
;	    ;WinMove(hwnd, "", x, y)
;        } catch {
;            MsgBox "Failed to move window with hwnd: " . hwnd
;        }
;        MsgBox "Found window with title: " . WinGetTitle("ahk_id " . hwnd)
;    }
;} catch {
;    MsgBox "No windows found with class name: " . className
;}
