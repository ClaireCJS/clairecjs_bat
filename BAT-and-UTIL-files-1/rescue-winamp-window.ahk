#SingleInstance Force
DetectHiddenWindows true
SetTitleMatchMode 2

WinampClass := "ahk_class Winamp v1.x"

hwnd := WinExist(WinampClass)
if !hwnd
    hwnd := WinExist("ahk_class Winamp v1")

if !hwnd {
    list := WinGetList("ahk_exe winamp.exe")
    for h in list {
        cls := WinGetClass(h)
        if InStr(cls, "Winamp") {
            hwnd := h
            break
        }
    }
    if !hwnd && list.Length
        hwnd := list[1]
}

if !hwnd {
    MsgBox "Couldn't find Winamp (Winamp v1.x / v1, or any window owned by winamp.exe)."
    ExitApp
}

MonitorGetWorkArea 1, &L, &T, &R, &B
x := L + 100, y := T + 100

WinShow hwnd
WinRestore hwnd
WinMove x, y, 275, 116, hwnd
WinActivate hwnd
