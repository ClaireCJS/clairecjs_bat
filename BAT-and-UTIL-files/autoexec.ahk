#SingleInstance

;;;;;;;; 
;;;;;;;;  2024 — What this does so far:
;;;;;;;; 
;;;;;;;;   * tooltips to tell you what your current insert mode is
;;;;;;;;   *  Ctrl+Hyphen for en dash ––
;;;;;;;;   *   Alt+Hyphen for em dash ——
;;;;;;;;   * similar things for *, !, and ?
;;;;;;;; 
;;;;;;;;   *  NOT WORKING AS OF 20240426 — Pause Winamp — Pause key, Ctrl-Shift-P      
;;;;;;;;   *  NOT WORKING AS OF 20240426 — Show  Winamp — Windows-W
;;;;;;;;
;;;;;;;; 





;;;;;;;;;;;;;;;;;;;;;;;; DASHES/etc ;;;;;;;;;;;;;;;;;;;;;;;;;
^?::Send "❔" ; Ctrl+? for ❔ [white]
!?::Send "❓" ;  Alt+? for ❓ [red]
^8::Send "⭐" ; Ctrl+8 for ⭐
!8::Send "🌟" ;  Alt+8 for 🌟
^-::Send "–" ; Ctrl+Hyphen for en dash 
!-::Send "—" ;  Alt+Hyphen for em dash
;;;;;;;;;;;;;;;;;;;;;;;; DASHES/etc ;;;;;;;;;;;;;;;;;;;;;;;;;

















;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; WINAMP ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; ; Stop, Windows-v, and Ctrl-Alt-V
;; #IfWinExist %WinampClass%
;; {
;;     Media_Stop::
;;     #v::
;;     ^!v::
;;     ControlSend, ahk_parent, v
;;     return
;; }
;; 
;; ; Next Track, Windows-b, and Ctrl-Alt-B
;; #IfWinExist %WinampClass%
;; {
;;     Media_Next::
;;     #b::
;;     ^!b::PP 
;;     ControlSend, ahk_parent, b
;;     return
;; }
;; 
;; ; Previous Track, Windows-z, and Ctrl-Alt-Z
;; #IfWinExist %WinampClass%
;; {
;;     Media_Prev::
;;     #z::
;;     ^!z::
;;     ControlSend, ahk_parent, z
;;     return
;; }

;;Winamp v1.x
^!p::
Pause::
#C::
{
    if not WinExist("ahk_class Winamp v1.x")
        return
    ; Otherwise, the above has set the "last found" window for use below.
        ControlSend "c"  ; Pause/Unpause
}

#W:: {
  WinActivate("*Winamp*")
}

;;     Pause::
;;     #c::
;;     ^!c::
;;     ControlSend, ahk_parent, c
;;     return
;; }
;; 
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; WINAMP ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;




; ToolTipOpt v1.004
; Changes:
;  v1.001 - Pass "Default" to restore a setting to default
;  v1.002 - ANSI compatibility
;  v1.003 - Added workarounds for ToolTip's parameter being overwritten
;           by code within the message hook.
;  v1.004 - Fixed text colour.
 
ToolTipFont(Options := "", Name := "", hwnd := "") {
    static hfont := 0
    if (hwnd = "")
        hfont := Options="Default" ? 0 : _TTG("Font", Options, Name), _TTHook()
    else
        DllCall("SendMessage", "ptr", hwnd, "uint", 0x30, "ptr", hfont, "ptr", 0)
}
 
ToolTipColor(Background := "", Text := "", hwnd := "") {
    static bc := "", tc := ""
    if (hwnd = "") {
        if (Background != "")
            bc := Background="Default" ? "" : _TTG("Color", Background)
        if (Text != "")
            tc := Text="Default" ? "" : _TTG("Color", Text)
        _TTHook()
    }
    else {
        ;GOAT VarSetCapacity(empty, 2, 0)
        DllCall("UxTheme.dll\SetWindowTheme", "ptr", hwnd, "ptr", 0
            , "ptr", (bc != "" && tc != "") ? &empty : 0)
        if (bc != "")
            DllCall("SendMessage", "ptr", hwnd, "uint", 1043, "ptr", bc, "ptr", 0)
        if (tc != "")
            DllCall("SendMessage", "ptr", hwnd, "uint", 1044, "ptr", tc, "ptr", 0)
    }
}
 
_TTHook() {
    static hook := 0
    ;goat if !hook
        ;goat hook := DllCall("SetWindowsHookExW", "int", 4            , "ptr", egisterCallback("_TTWndProc"), "ptr", 0            , "uint", DllCall("GetCurrentThreadId"), "ptr")
}
 
_TTWndProc(nCode, _wp, _lp) {
    Critical 999
   ;lParam  := NumGet(_lp+0*A_PtrSize)
   ;wParam  := NumGet(_lp+1*A_PtrSize)
    uMsg    := NumGet(_lp+2*A_PtrSize, "uint")
    ;goat hwnd    := NumGet(_lp+3*A_PtrSize)
    if (nCode >= 0 && (uMsg = 1081 || uMsg = 1036)) {
        ;goat _hack_ := ahk_id %hwnd%
        ;goat WinGetClass wclass, %_hack_%
        ;goat if (wclass = "tooltips_class32") {
        ;goat     ToolTipColor(,, hwnd)
        ;goat     ToolTipFont(,, hwnd)
        ;goat }
    }
    return DllCall("CallNextHookEx", "ptr", 0, "int", nCode, "ptr", _wp, "ptr", _lp, "ptr")
}
 
_TTG(Cmd, Arg1, Arg2 := "") {
    static htext := 0, hgui := 0
    if !htext {
        ;GOAT Gui _TTG: Add, Text, +hwndhtext
        ;GOAT Gui _TTG: +hwndhgui +0x40000000
    }
    ;GOAT Gui _TTG: %Cmd%, %Arg1%, %Arg2%
    ;goat if (Cmd = "Font") {
        ;GOAT GuiControl _TTG: Font, %htext%
        ;goat SendMessage 0x31, 0, 0,, ahk_id %htext%
        ;goat return ErrorLevel
    ;goat }
    if (Cmd = "Color") {
        hdc := DllCall("GetDC", "ptr", htext, "ptr")
        ;goat SendMessage 0x138, hdc, htext,, ahk_id %hgui%
        ;goat clr := DllCall("GetBkColor", "ptr", hdc, "uint")
        ;goat DllCall("ReleaseDC", "ptr", htext, "ptr", hdc)
        ;goat return clr
    }
}







;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; INSERT MODE TOOLTIP ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;#Include c:\bat\ShinsOverlayClass.ahk
#Include c:\bat\ToolTipOptions.ahk

; Check if the active window is the TCC window with the given class name
Persistent
global overwrite_mode := 0  ; Initialize the global overwrite_mode variable
Insert::
{
    ;f WinActive("ahk_class Windows.UI.Composition.DesktopWindowContentBridge") 
    if WinActive("TCC") {
        global overwrite_mode  ; Ensure we're using the global overwrite_mode variable
        overwrite_mode := !overwrite_mode  ; overwrite_mode the state
        ToolTipFont("s20", "Gill Sans Ultra Bold")
        if (overwrite_mode) {
            ansiCode := Chr(27) "[4 q"  ; ANSI code for steady underline cursor
            text1 := "—————— OVERWRITE mode —————— `n—————— OVERWRITE mode —————— `n—————— OVERWRITE mode —————— `n—————— OVERWRITE mode —————— `n—————— OVERWRITE mode —————— `n—————— OVERWRITE mode —————— `n"
            text  := "      ███                                              █                       `n     █   █                                                    █                `n    █     █                                                   █                `n    █     █ ███ ███  █████  ███ ██  ███ ███ ███ ██   ███     ████    █████     `n    █     █  █   █  █     █   ██  █  █   █    ██  █    █      █     █     █    `n    █     █  █   █  ███████   █      █ █ █    █        █      █     ███████    `n    █     █   █ █   █         █      █ █ █    █        █      █     █          `n     █   █    █ █   █     █   █       █ █     █        █      █  █  █     █    `n      ███      █     █████  █████     █ █   █████    █████     ██    █████     `n"
        } Else {
            ansiCode := Chr(27) "[2 q"  ; ANSI code for blinking block cursor
            text1 := " —————— INSERT mode —————— `n —————— INSERT mode —————— `n —————— INSERT mode —————— `n —————— INSERT mode —————— `n —————— INSERT mode —————— `n —————— INSERT mode —————— "
            text  := "    █████                                            `n      █                                      █       `n      █                                      █       `n      █    ██ ██    █████   █████  ███ ██   ████     `n      █     ██  █  █     █ █     █   ██  █   █       `n      █     █   █   ███    ███████   █       █       `n      █     █   █      ██  █         █       █       `n      █     █   █  █     █ █     █   █       █  █    `n    █████  ███ ███  █████   █████  █████      ██     `n"


        }
        ;SendInput(ansiCode)     ; Send the ANSI code using SendInput

        margin:= 50
        x_offset := 240                   ;higher #s == move box left — 250 is too much
        y_offset := 110                   ;higher #s == move box up
        if (overwrite_mode) {
            x_offset := x_offset + 90     
        }
        ToolTipOptions.Init()
        ToolTipOptions.SetFont("s10 norm", "Consolas Bold")
        ToolTipOptions.SetMargins(margin, margin, margin, margin)
        ;oolTipOptions.SetTitle("" , 4)
        ToolTipOptions.SetColors("White", "Blue")
        ;oolTip("Hello world!")
        ToolTip    text, A_ScreenWidth //2 - x_offset, A_ScreenHeight//2 - y_offset
        ;oolTip    text, A_ScreenWidth //2           , A_ScreenHeight//2            
        SetTimer(() => ToolTip("", 0), 750)    ; Optionally, hide the tooltip after a short delay


        CoordMode "ToolTip", "Screen"
        TrayTip    ".`n" text1
        SetTimer () =>TrayTip(), -1000


    
    }
    Send("{Insert}")  
    Return
}
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; INSERT MODE TOOLTIP ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

