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


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; INSERT MODE TOOLTIP ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;#Include c:\bat\ShinsOverlayClass.ahk
#Include c:\bat\ToolTipOptions.ahk
Persistent
global    insert_mode             := 0  
global  num_lock_mode             := 0
;lobal caps_lock_mode             := 0
global     dummy_mode             := 0  ;used to avoid passing caps lock mode because we manage that in the outer layer, but the other 2 in the inner layer
                                  
global insert_up_tooltip_text     := " —————— INSERT mode —————— `n —————— INSERT mode —————— `n —————— INSERT mode —————— `n —————— INSERT mode —————— `n —————— INSERT mode —————— `n —————— INSERT mode —————— "
global insert_dn_tooltip_text     := " ———— OVERWRITE mode ————— `n ———— OVERWRITE mode ————— `n ———— OVERWRITE mode ————— `n ———— OVERWRITE mode ————— `n ———— OVERWRITE mode ————— `n ———— OVERWRITE mode ————— "
global insert_up_popup_text       := "      ███                                              █                       `n     █   █                                                    █                `n    █     █                                                   █                `n    █     █ ███ ███  █████  ███ ██  ███ ███ ███ ██   ███     ████    █████     `n    █     █  █   █  █     █   ██  █  █   █    ██  █    █      █     █     █    `n    █     █  █   █  ███████   █      █ █ █    █        █      █     ███████    `n    █     █   █ █   █         █      █ █ █    █        █      █     █          `n     █   █    █ █   █     █   █       █ █     █        █      █  █  █     █    `n      ███      █     █████  █████     █ █   █████    █████     ██    █████     `n"
global insert_dn_popup_text       := "    █████                                            `n      █                                      █       `n      █                                      █       `n      █    ██ ██    █████   █████  ███ ██   ████     `n      █     ██  █  █     █ █     █   ██  █   █       `n      █     █   █   ███    ███████   █       █       `n      █     █   █      ██  █         █       █       `n      █     █   █  █     █ █     █   █       █  █    `n    █████  ███ ███  █████   █████  █████      ██     `n"
                                  
global numLock_up_tooltip_text    := " —————— NUM LOCK OFF —————— `n —————— NUM LOCK OFF —————— `n —————— NUM LOCK OFF —————— `n —————— NUM LOCK OFF —————— `n —————— NUM LOCK OFF —————— `n —————— NUM LOCK OFF —————— "
global numLock_dn_tooltip_text    := " —————— NUM LOCK ON ——————— `n —————— NUM LOCK ON ——————— `n —————— NUM LOCK ON ——————— `n —————— NUM LOCK ON ——————— `n —————— NUM LOCK ON ——————— `n —————— NUM LOCK ON ——————— "
global numLock_up_popup_text      := " —————— NUM LOCK OFF —————— `n —————— NUM LOCK OFF —————— `n —————— NUM LOCK OFF —————— `n —————— NUM LOCK OFF —————— `n —————— NUM LOCK OFF —————— `n —————— NUM LOCK OFF —————— "
global numLock_dn_popup_text      := " —————— NUM LOCK ON ——————— `n —————— NUM LOCK ON ——————— `n —————— NUM LOCK ON ——————— `n —————— NUM LOCK ON ——————— `n —————— NUM LOCK ON ——————— `n —————— NUM LOCK ON ——————— "
                                  
global capsLock_up_tooltip_text   := " ————— caps lock off —————— `n ————— caps lock off —————— `n ————— caps lock off —————— `n ————— caps lock off —————— `n ————— caps lock off —————— `n ————— caps lock off —————— "
global capsLock_dn_tooltip_text   := " —————— CAPS LOCK ON —————— `n —————— CAPS LOCK ON —————— `n —————— CAPS LOCK ON —————— `n —————— CAPS LOCK ON —————— `n —————— CAPS LOCK ON —————— `n —————— CAPS LOCK ON —————— "
global capsLock_up_popup_text     := " ————— caps lock off —————— `n ————— caps lock off —————— `n ————— caps lock off —————— `n ————— caps lock off —————— `n ————— caps lock off —————— `n ————— caps lock off —————— "
global capsLock_dn_popup_text     := " —————— CAPS LOCK ON —————— `n —————— CAPS LOCK ON —————— `n —————— CAPS LOCK ON —————— `n —————— CAPS LOCK ON —————— `n —————— CAPS LOCK ON —————— `n —————— CAPS LOCK ON —————— "

global scrollLock_up_tooltip_text := " ———— scroll lock off ————— `n ———— scroll lock off ————— `n ———— scroll lock off ————— `n ———— scroll lock off ————— `n ———— scroll lock off ————— `n ———— scroll lock off ————— "
global scrollLock_dn_tooltip_text := " ————— scroll lock on ————— `n ————— scroll lock on ————— `n ————— scroll lock on ————— `n ————— scroll lock on ————— `n ————— scroll lock on ————— `n ————— scroll lock on ————— "
global scrollLock_up_popup_text   := " ———— scroll lock off ————— `n ———— scroll lock off ————— `n ———— scroll lock off ————— `n ———  scroll lock off ————— `n ———— scroll lock off ————— `n ———— scroll lock off ————— "
global scrollLock_dn_popup_text   := " ————— scroll lock on ————— `n ————— scroll lock on ————— `n ————— scroll lock on ————— `n ————— scroll lock on ————— `n ————— scroll lock on ————— `n ————— scroll lock on ————— "

Insert::   
{ 
    Send      "{Insert}"  
    HandleKey( "Insert"   ,    "insert_mode",   insert_up_tooltip_text,   insert_dn_tooltip_text,   insert_up_popup_text,   insert_dn_popup_text,               "[2 q",               "[4 q") 
}
NumLock:: 
{ 
    if (GetKeyState("NumLock", "T")) {
        SetNumLockState("Off")                                ; Turn Num Lock Off
    } else {                                                   
        SetNumLockState( "On")                                ; Turn Num Lock On
    }
    HandleKey( "NumLock"  ,  "num_lock_mode",  numLock_up_tooltip_text,  numLock_dn_tooltip_text,  numLock_up_popup_text,  numLock_dn_popup_text,               "[2 q",               "[4 q") 
}
CapsLock:: 
{ 
    if (GetKeyState("CapsLock", "T")) {
        SetCapsLockState("Off")                               ; Turn Caps Lock Off
    } else {                                                   
        SetCapsLockState( "On")                               ; Turn Caps Lock On
    }
    HandleKey( "CapsLock" ,     "dummy_mode", capsLock_up_tooltip_text, capsLock_dn_tooltip_text, capsLock_up_popup_text, capsLock_dn_popup_text,               "[2 q",               "[4 q") 
}
ScrollLock:: 
{ 
    if (GetKeyState("ScrollLock", "T")) {
        SetScrollLockState("Off")                             ; Turn Scroll Lock Off
    } else {                                                   
        SetScrollLockState( "On")                             ; Turn Scroll Lock On
    }
    HandleKey("ScrollLock",     "dummy_mode", scrollLock_up_tooltip_text, scrollLock_dn_tooltip_text, scrollLock_up_popup_text, scrollLock_dn_popup_text,               "[2 q",               "[4 q") 
}
HandleKey(      KeyName   ,       KeyModeVar,      key_up_tooltip_text,      key_dn_tooltip_text,      key_up_popup_text,      key_dn_popup_text, key_up_ansi_code_exp, key_dn_ansi_code_exp) 
{
    global      insert_mode          
    ;lobal   caps_lock_mode          
    global    num_lock_mode                                             
    global scroll_lock_mode                                             
    global       dummy_mode                                             
    global insert_up_tooltip_text  
    global insert_dn_tooltip_text  
    global insert_up_popup_text    
    global insert_dn_popup_text    
    global capsLock_up_tooltip_text
    global capsLock_dn_tooltip_text
    global capsLock_up_popup_text  
    global capsLock_dn_popup_text  
    global numLock_up_tooltip_text 
    global numLock_dn_tooltip_text 
    global numLock_up_popup_text   
    global numLock_dn_popup_text   
    global scrollLock_up_tooltip_text 
    global scrollLock_dn_tooltip_text 
    global scrollLock_up_popup_text   
    global scrollLock_dn_popup_text   

    ;if WinActive("TCC") {
    ;global          %KeyModeVar%                           ; Ensure we're using the global key mode variable
    %KeyModeVar% := !%KeyModeVar%                           ; Toggle the key mode state
    ToolTipFont("s20", "Gill Sans Ultra Bold")
    if (%KeyModeVar%) {
        ansiCode := Chr(27) key_dn_ansi_code_exp            ; experimental, doesn't work
        text1    :=         key_dn_tooltip_text
        text     :=         key_dn_popup_text
    } else {
        ansiCode := Chr(27) key_up_ansi_code_exp            ; experimental, doesn't work
        text1    :=         key_up_tooltip_text
        text     :=         key_up_popup_text
    }
    margin   := 50
    x_offset := 240                                         ; higher #s == move box left — 250 is too much
    y_offset := 110                                         ; higher #s == move box up
    if (insert_mode) {
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
    SetTimer(() => ToolTip("", 0), 750)                     ; Optionally, hide the tooltip after a short delay

    CoordMode "ToolTip", "Screen"
    TrayTip    ".`n" text1
    SetTimer () =>TrayTip(), -1000
    ;}
    return
}
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; INSERT MODE TOOLTIP ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;




;;;;;;;;;;;;;;;;;;;;;;;;;; TOOLTIP UTILITY FUNCTIONS ;;;;;;;;;;;;;;;;;;;;;;;;;;;
; ToolTipOpt v1.004
; Changes:
;  v1.001 - Pass "Default" to restore a setting to default
;  v1.002 - ANSI compatibility
;  v1.003 - Added workarounds for ToolTip's parameter being overwritten by code within the message hook.
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
        ;🐐 VarSetCapacity(empty, 2, 0)
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
    ;🐐 if !hook
        ;🐐 hook := DllCall("SetWindowsHookExW", "int", 4            , "ptr", egisterCallback("_TTWndProc"), "ptr", 0            , "uint", DllCall("GetCurrentThreadId"), "ptr")
}
 
_TTWndProc(nCode, _wp, _lp) {
    Critical 999
   ;lParam  := NumGet(_lp+0*A_PtrSize)
   ;wParam  := NumGet(_lp+1*A_PtrSize)
    uMsg    := NumGet(_lp+2*A_PtrSize, "uint")
    ;🐐 hwnd    := NumGet(_lp+3*A_PtrSize)
    if (nCode >= 0 && (uMsg = 1081 || uMsg = 1036)) {
        ;🐐 _hack_ := ahk_id %hwnd%
        ;🐐 WinGetClass wclass, %_hack_%
        ;🐐 if (wclass = "tooltips_class32") {
        ;🐐     ToolTipColor(,, hwnd)
        ;🐐     ToolTipFont(,, hwnd)
        ;🐐 }
    }
    return DllCall("CallNextHookEx", "ptr", 0, "int", nCode, "ptr", _wp, "ptr", _lp, "ptr")
}
 
_TTG(Cmd, Arg1, Arg2 := "") {
    static htext := 0, hgui := 0
    if !htext {
        ;🐐 Gui _TTG: Add, Text, +hwndhtext
        ;🐐 Gui _TTG: +hwndhgui +0x40000000
    }
    ;🐐 Gui _TTG: %Cmd%, %Arg1%, %Arg2%
    ;🐐 if (Cmd = "Font") {
        ;🐐 GuiControl _TTG: Font, %htext%
        ;🐐 SendMessage 0x31, 0, 0,, ahk_id %htext%
        ;🐐 return ErrorLevel
    ;🐐 }
    if (Cmd = "Color") {
        hdc := DllCall("GetDC", "ptr", htext, "ptr")
        ;🐐 SendMessage 0x138, hdc, htext,, ahk_id %hgui%
        ;🐐 clr := DllCall("GetBkColor", "ptr", hdc, "uint")
        ;🐐 DllCall("ReleaseDC", "ptr", htext, "ptr", hdc)
        ;🐐 return clr
    }
}
;;;;;;;;;;;;;;;;;;;;;;;;;; TOOLTIP UTILITY FUNCTIONS ;;;;;;;;;;;;;;;;;;;;;;;;;;;












;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; WINAMP ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 🌟🌟🌟 NOT WORKING WELL!! 🌟🌟🌟
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








;;;;;;;;;;;;;;;;;;;;;;;; DASHES/etc ;;;;;;;;;;;;;;;;;;;;;;;;;
^?::Send "❔" ; Ctrl+? for ❔ [white]
!?::Send "❓" ;  Alt+? for ❓ [red]
^8::Send "⭐" ; Ctrl+8 for ⭐
!8::Send "🌟" ;  Alt+8 for 🌟
^-::Send "–" ; Ctrl+Hyphen for en dash 
!-::Send "—" ;  Alt+Hyphen for em dash
;;;;;;;;;;;;;;;;;;;;;;;; DASHES/etc ;;;;;;;;;;;;;;;;;;;;;;;;;


;;;;;;;;;;;;;;;; INITIAL STATE FOR TRACKED KEYS ;;;;;;;;;;;;;;;;
;(insert is handled completely differently, no way to track it)
if (GetKeyState("CapsLock", "T")) {
    SetCapsLockState("On")
} else {
    SetCapsLockState("Off")
}
if (GetKeyState("NumLock", "T")) {
    SetNumLockState("On")
} else {
    SetNumLockState("Off")
}
if (GetKeyState("ScrollLock", "T")) {
    SetScrollLockState("On")
} else {
    SetScrollLockState("Off")
}
;;;;;;;;;;;;;;;; INITIAL STATE FOR TRACKED KEYS ;;;;;;;;;;;;;;;;

