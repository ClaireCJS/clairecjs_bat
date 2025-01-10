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
global      insert_mode         := 0  
global    num_lock_mode         := 0
global   caps_lock_mode         := 0
global scroll_lock_mode         := 0
global       dummy_mode         := 0  ;used to avoid passing caps lock mode because we manage that in the outer layer, but the other 2 in the inner layer
                                
;TODO 🐐 finish the large renderings of the other ones haha

global insert_up_tray_text        := " ———— OVERWRITE mode ————— `n ———— OVERWRITE mode ————— `n ———— OVERWRITE mode ————— `n ———— OVERWRITE mode ————— `n ———— OVERWRITE mode ————— `n ———— OVERWRITE mode ————— "
global insert_dn_tray_text        := " —————— INSERT mode —————— `n —————— INSERT mode —————— `n —————— INSERT mode —————— `n —————— INSERT mode —————— `n —————— INSERT mode —————— `n —————— INSERT mode —————— "
global insert_up_popup_text       := "      ███                                              █                       `n     █   █                                                    █                `n    █     █                                                   █                `n    █     █ ███ ███  █████  ███ ██  ███ ███ ███ ██   ███     ████    █████     `n    █     █  █   █  █     █   ██  █  █   █    ██  █    █      █     █     █    `n    █     █  █   █  ███████   █      █ █ █    █        █      █     ███████    `n    █     █   █ █   █         █      █ █ █    █        █      █     █          `n     █   █    █ █   █     █   █       █ █     █        █      █  █  █     █    `n      ███      █     █████  █████     █ █   █████    █████     ██    █████     `n"
global insert_dn_popup_text       := "    ████                                            `n      █                                      █       `n      █                                      █       `n      █    ██ ██    █████   █████  ███ ██   ████     `n      █     ██  █  █     █ █     █   ██  █   █       `n      █     █   █   ███    ███████   █       █       `n      █     █   █      ██  █         █       █       `n      █     █   █  █     █ █     █   █       █  █    `n    █████  ███ ███  █████   █████  █████      ██     `n"

global numLock_up_tray_text       := " —————— NUM LOCK OFF —————— `n —————— NUM LOCK OFF —————— `n —————— NUM LOCK OFF —————— `n —————— NUM LOCK OFF —————— `n —————— NUM LOCK OFF —————— `n —————— NUM LOCK OFF —————— "
global numLock_dn_tray_text       := " —————— NUM LOCK ON ——————— `n —————— NUM LOCK ON ——————— `n —————— NUM LOCK ON ——————— `n —————— NUM LOCK ON ——————— `n —————— NUM LOCK ON ——————— `n —————— NUM LOCK ON ——————— "
global numLock_up_popup_text_OLD  := " —————— NUM LOCK OFF —————— `n —————— NUM LOCK OFF —————— `n —————— NUM LOCK OFF —————— `n —————— NUM LOCK OFF —————— `n —————— NUM LOCK OFF —————— `n —————— NUM LOCK OFF —————— "
global numLock_up_popup_text      := "    ██  ███                █████                   ██                ███      ███    ███    `n     █   █                   █                      █               █   █    █      █       `n     ██  █                   █                      █              █     █   █      █       `n     ██  █ ██  ██  ███ █     █      █████   █████   █  ██          █     █  ████   ████     `n     █ █ █  █   █   █ █ █    █     █     █ █     █  █  █           █     █   █      █       `n     █  ██  █   █   █ █ █    █     █     █ █        █ █            █     █   █      █       `n     █  ██  █   █   █ █ █    █     █     █ █        ███            █     █   █      █       `n     █   █  █  ██   █ █ █    █   █ █     █ █     █  █  █            █   █    █      █       `n    ███  █   ██ ██ ██ █ ██ ███████  █████   █████  ██   ██           ███    ████   ████     `n"
global numLock_dn_popup_text_OLD  := " —————— NUM LOCK ON ——————— `n —————— NUM LOCK ON ——————— `n —————— NUM LOCK ON ——————— `n —————— NUM LOCK ON ——————— `n —————— NUM LOCK ON ——————— `n —————— NUM LOCK ON ——————— "
global numLock_dn_popup_text      := "    ██  ███                 █████                   ██                ███              `n     █   █                    █                      █               █   █             `n     ██  █                    █                      █              █     █            `n     ██  █  ██  ██  ███ █     █      █████   █████   █  ██          █     █ ██ ██      `n     █ █ █   █   █   █ █ █    █     █     █ █     █  █  █           █     █  ██  █     `n     █  ██   █   █   █ █ █    █     █     █ █        █ █            █     █  █   █     `n     █  ██   █   █   █ █ █    █     █     █ █        ███            █     █  █   █     `n     █   █   █  ██   █ █ █    █   █ █     █ █     █  █  █            █   █   █   █     `n    ███  █    ██ ██ ██ █ ██ ███████  █████   █████  ██   ██           ███   ███ ███    `n"                                

global capsLock_up_tray_text      := " ————— caps lock off —————— `n ————— caps lock off —————— `n ————— caps lock off —————— `n ————— caps lock off —————— `n ————— caps lock off —————— `n ————— caps lock off —————— "
global capsLock_dn_tray_text      := " —————— CAPS LOCK ON —————— `n —————— CAPS LOCK ON —————— `n —————— CAPS LOCK ON —————— `n —————— CAPS LOCK ON —————— `n —————— CAPS LOCK ON —————— `n —————— CAPS LOCK ON —————— "
global capsLock_up_popup_text_OLD := " ————— caps lock off —————— `n ————— caps lock off —————— `n ————— caps lock off —————— `n ————— caps lock off —————— `n ————— caps lock off —————— `n ————— caps lock off —————— "
global capsLock_up_popup_text     := "                                              ██                    ██                         ██      ██    `n                                               █                     █                        █       █	     `n                                               █                     █                        █       █	     `n     █████   ████   ██████   █████             █     █████   █████   █  ██           █████   ████    ████    `n    █     █      █   █    █ █     █            █    █     █ █     █  █  █           █     █   █       █	     `n    █        █████   █    █  ███               █    █     █ █        █ █            █     █   █       █	     `n    █       █    █   █    █     ██             █    █     █ █        ███            █     █   █       █	     `n    █     █ █    █   █    █ █     █            █    █     █ █     █  █  █           █     █   █       █	     `n     █████   ████ █  █████   █████           █████   █████   █████  ██   ██          █████   ████    ████    `n                     █											     `n                    ███											     `n		   											     `n"
global capsLock_dn_popup_text_OLD := " —————— CAPS LOCK ON —————— `n —————— CAPS LOCK ON —————— `n —————— CAPS LOCK ON —————— `n —————— CAPS LOCK ON —————— `n —————— CAPS LOCK ON —————— `n —————— CAPS LOCK ON —————— "
global capsLock_dn_popup_text     := "      ████    ██    ██████   █████          █████     ███     ████  ███  ██           ███   ██  ███    `n     █    █    █     █    █ █     █           █      █   █   █    █  █   █           █   █   █   █     `n    █          █     █    █ █                 █     █     █ █        █  █           █     █  ██  █     `n    █         █ █    █    █ █                 █     █     █ █        █  █           █     █  ██  █     `n    █         █ █    █████   █████            █     █     █ █        █ █            █     █  █ █ █     `n    █        █   █   █            █           █     █     █ █        ███            █     █  █  ██     `n    █        █████   █            █           █     █     █ █        █  █           █     █  █  ██     `n     █    █  █   █   █      █     █           █   █  █   █   █    █  █   █           █   █   █   █     `n      ████  ███ ███ ████     █████          ███████   ███     ████  ███  ██           ███   ███  █     `n"

global scrollLock_up_tray_text    := " ———— scroll lock off ————— `n ———— scroll lock off ————— `n ———— scroll lock off ————— `n ———— scroll lock off ————— `n ———— scroll lock off ————— `n ———— scroll lock off ————— "
global scrollLock_dn_tray_text    := " ————— scroll lock on ————— `n ————— scroll lock on ————— `n ————— scroll lock on ————— `n ————— scroll lock on ————— `n ————— scroll lock on ————— `n ————— scroll lock on ————— "
global scrollLock_up_popup_text   := " ———— scroll lock off ————— `n ———— scroll lock off ————— `n ———— scroll lock off ————— `n ———  scroll lock off ————— `n ———— scroll lock off ————— `n ———— scroll lock off ————— "
global scrollLock_dn_popup_text   := " ————— scroll lock on ————— `n ————— scroll lock on ————— `n ————— scroll lock on ————— `n ————— scroll lock on ————— `n ————— scroll lock on ————— `n ————— scroll lock on ————— "

Insert::   
{ 
    Send      "{Insert}"  
    HandleKey( "Insert"   ,      "insert_mode",     insert_up_tray_text,     insert_dn_tray_text,     insert_up_popup_text,     insert_dn_popup_text,               "[2 q",               "[4 q") 
}
NumLock:: 
{ 
    if (GetKeyState("NumLock", "T")) {
        SetNumLockState("Off")                                ; Turn Num Lock Off
    } else {                                                   
        SetNumLockState( "On")                                ; Turn Num Lock On
    }
    HandleKey( "NumLock"  ,    "num_lock_mode",    numLock_up_tray_text,    numLock_dn_tray_text,    numLock_up_popup_text,    numLock_dn_popup_text,              "dummy",              "dummy") 
}
CapsLock:: 
{ 
    if (GetKeyState("CapsLock", "T")) {
        SetCapsLockState("Off")                               ; Turn Caps Lock Off
    } else {                                                   
        SetCapsLockState( "On")                               ; Turn Caps Lock On
    }
    HandleKey( "CapsLock" ,   "caps_lock_mode",   capsLock_up_tray_text,   capsLock_dn_tray_text,   capsLock_up_popup_text,   capsLock_dn_popup_text,              "dummy",              "dummy") 
}
ScrollLock:: 
{ 
    if (GetKeyState("ScrollLock", "T")) {
        SetScrollLockState("Off")                             ; Turn Scroll Lock Off
    } else {                                                   
        SetScrollLockState( "On")                             ; Turn Scroll Lock On
    }
    HandleKey("ScrollLock", "scroll_lock_mode", scrollLock_up_tray_text, scrollLock_dn_tray_text, scrollLock_up_popup_text, scrollLock_dn_popup_text,              "dummy",              "dummy") 
}
HandleKey(      KeyName   ,     KeyModeVarName,        key_up_tray_text,        key_dn_tray_text,        key_up_popup_text,        key_dn_popup_text, key_up_ansi_code_exp, key_dn_ansi_code_exp) 
{
    global               dummy_mode                                             
    global              insert_mode          
    global           caps_lock_mode          
    global            num_lock_mode                                             
    global         scroll_lock_mode                                             
    global      insert_up_tray_text  
    global      insert_dn_tray_text  
    global     insert_up_popup_text    
    global     insert_dn_popup_text    
    global    capsLock_up_tray_text
    global    capsLock_dn_tray_text
    global   capsLock_up_popup_text  
    global   capsLock_dn_popup_text  
    global     numLock_up_tray_text 
    global     numLock_dn_tray_text 
    global    numLock_up_popup_text   
    global    numLock_dn_popup_text   
    global  scrollLock_up_tray_text 
    global  scrollLock_dn_tray_text 
    global scrollLock_up_popup_text   
    global scrollLock_dn_popup_text   

    ;if WinActive("TCC")                                                 ; originally the entire rest of the block here was for TCC-only to try to change the cursor shape with ANSI codes, but that was impossible
    %KeyModeVarName% := !%KeyModeVarName%                                ; Toggle the key mode state
    if (%KeyModeVarName%) {                                            
        ;ansiCode  := Chr(27) key_dn_ansi_code_exp                       ; experimental, doesn't work, abandoned
        tray_text  :=         key_dn_tray_text                         
        popup_text :=         key_dn_popup_text                        
    } else {                                                           
        ;ansiCode  := Chr(27) key_up_ansi_code_exp                       ; experimental, doesn't work, abandoned
        tray_text  :=         key_up_tray_text                         
        popup_text :=         key_up_popup_text                        
    }                                                                  
    margin   := 50                                                     
    x_offset := 300                                                      ; higher #s == move box left — 250 is too much AT FIRST but then added others —— this one is trial and error, yuck
    y_offset := 110                                                      ; higher #s == move box up
    if (insert_mode) {                                                 
        x_offset := x_offset + 90                                        ; the word 'overwrite' is longer than 'insert', so move it this much more
    }
    ToolTipOptions.Init()
    ToolTipOptions.SetFont(       "s10 norm","Consolas Bold")
    ToolTipOptions.SetMargins(margin, margin, margin, margin)
    ToolTipOptions.SetTitle(" " , 4)                                     ; makes a blue exclaimation mark on the pop-up box to the left of our text
    ToolTipOptions.SetColors("White", "Blue")
    ToolTip popup_text, A_ScreenWidth //2 - x_offset, A_ScreenHeight//2 - y_offset
    SetTimer(() => ToolTip("", 0), 750)                                  ; hide the on-screen banner  after these many ms

    CoordMode "ToolTip", "Screen"
    TrayTip   "⚠`n" tray_text   
    SetTimer () =>TrayTip(), -1000                                       ; hide the tray notificatiOn after these many ms
    return
}
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; INSERT MODE TOOLTIP ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;










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
        return           ; Otherwise, the above has set the "last found" window for use below.
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








;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; DASHES/etc ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
^?::Send  "❔"		;	    Ctrl+? for ❔ [white]
!?::Send  "❓"		;	     Alt+? for ❓ [red]
^!?::Send "⁉️"		;	Ctrl-Alt+? for ⁉️ 

;can't figure out Ctrl-Alt-! though ...      ^!!:Send  "‼️";
^!::Send  "❕"		;	    Ctrl+! for ❕ [white]
!!::Send  "❗"		;	     Alt+! for ❗ [red]
		         
^8::Send  "⭐"		;	Ctrl+8 for ⭐
!8::Send  "🌟"		;	Alt+8 for 🌟
		         
;-------   "-"          ;           Hyphen --------- for normal default hyphen                     (compound words, words interrupted by line break)
^-::Send   "–"          ;      Ctrl+Hyphen ––––––––– for en dash                                   (ranges,    quotations)
!-::Send   "—"          ;       Alt+Hyphen ————————— for em dash                                   (interruptions, breaks)
;;;;;;;;;  "─"          ;                  ───────── for unicode box drawing light horizontal      (      dividers       ) WHICH LOOKS SAME AS ENDASH usually
^!-::Send  "━"          ;  Ctrl-Alt+Hyphen ━━━━━━━━━ for unicode box drawing heavy horizontal line (      dividers       )
      
!'::Send  "{U+0027}"    ;      Alt+apostrophe for    default original dumb apostrophe / feet symbol
'::Send   "’"           ;          apostrophe for ’  smart single quote: right           ; the *correct* apostrophe we should be using, i.e. “can’t”
^'::Send  "‘"           ;     Ctrl+apostrophe for ‘  smart single quote: left
^!'::Send "‘’"          ; Ctrl-Alt+apostrophe for ‘’ smart single quotes: both
		         
^"::Send  "“"           ;     Ctrl+quote for “  smart double/normal quotes: left
!"::Send  "”"           ;      Alt+quote for ”  smart double/normal quotes: right
^!"::Send "“”"          ; Ctrl+Alt+quote for “” smart double/normal quotes: both
;(normal quote key)     ;          quote for "  default original dumb quote / inches symbol

; ,::Send   "❟"		;          Comma for “❟” smart comma / fancy unicode comma [in editplus, it looks “dumber” (“❟”) than the “dumb” comma (“,”)
;^,::Send  "{U+2C}"	;     Ctrl-Comma for “,” dumb comma / original/normal comma but Windows Terminal overrides this
;!,::Send  "{U+2C}"	;      Alt-Comma for “,” dumb comma / original/normal comma
;^!,::Send "{U+2C}"	; Ctrl-Alt-Comma for “,” dumb comma / original/normal comma

;,::Send  ","		;          Comma for “,” the normal comma key we’re all used —— the “dumb” comma / original comma / “normal” comma 
^,::Send  "❟"		;     Ctrl-Comma for “,” smart comma /	fancy unicode comma —— but Windows Terminal overrides this
!,::Send  "❟"		;      Alt-Comma for “❟”  smart comma /	fancy unicode comma [in editplus, it looks “dumber” (“❟”) than the “dumb” comma (“,”)
^!,::Send "❟"		; Ctrl-Alt-Comma for “❟”  smart comma /	fancy unicode comma [in editplus, it looks “dumber” (“❟”) than the “dumb” comma (“,”)


		      
^!0::Send "⁰"           ; Ctrl+Alt+0 for superscript number
^!1::Send "¹"           ; Ctrl+Alt+1 for superscript number
^!2::Send "²"           ; Ctrl+Alt+2 for superscript number
^!3::Send "³"           ; Ctrl+Alt+3 for superscript number
^!4::Send "⁴"           ; Ctrl+Alt+4 for superscript number
^!5::Send "⁵"           ; Ctrl+Alt+5 for superscript number
^!6::Send "⁶"           ; Ctrl+Alt+6 for superscript number
^!7::Send "⁷"           ; Ctrl+Alt+7 for superscript number
^!8::Send "⁸"           ; Ctrl+Alt+8 for superscript number
^!9::Send "⁹"           ; Ctrl+Alt+9 for superscript number
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; DASHES/etc ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;


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

