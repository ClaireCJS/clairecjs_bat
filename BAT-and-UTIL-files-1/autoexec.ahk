#SingleInstance

;;;;;;;; 
;;;;;;;;  2025 — What this does so far:
;;;;;;;; 
;;;;;;;;   ✨ pop-ups to tell you what your current insert/CapsLock/ScrollLock/NumLock mode is
;;;;;;;; 
;;;;;;;;   ✨ additonal key mappings —— Generally speaking:  Ctrl- & Alt- for more, then Ctrl-Alt- for “most dramatic” version, and sometimes Win-Alt-{key} or Ctrl-Alt-Win-{key} or other combos 
;;;;;;;;         ✪ Ctrl-CapsLock                Generates an "ENTER" keypress aka “Lefthanded Enter Key substitute”
;;;;;;;;         ✪ Example: Smart Quotes:       Ctrl-Alt-" to create “”, Ctrl-Shift-" for “, Alt-Shift-" for ”
;;;;;;;;         ✪ Example: Smart Apostrophes:  ' key is now makes ’, so you have to use Alt-' to get the original '
;;;;;;;;         ✪ Example: Smart Comma:        Hit Alt-, for ❟ —— the “smart comma”
;;;;;;;;         ✪ Example: X:                  ctrl-x and alt-x would be reserved, but ctrl-alt-X=× the multiply symbol, and ctrl-alt-shift-x=✖️ the emoji
;;;;;;;;         ✪ Many others
;;;;;;;; 
;;;;;;;;   ✨ Some amount of WinAmp control which may or may not be working because I use WinAmp’s internal global hotkeys and Girder for various automations so I’m never quite sure
;;;;;;;;         × WinAmp pause: use Pause-Key / Ctrl-Shift-P / Windows-C (if you don’t have Cortana)
;;;;;;;;         × WinAmp show:  Windows-W is working, but we set Ctrl-Alt-W within WinAmp’s global hotkeys
;;;;;;;;
;;;;;;;; 














;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; KEYBOARD ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;todo these brackets: 【a】 [a] [-] 【-】_【-】 [-]_[-]





;;;;; NUMBER & PUNCTUATION KEYS ROW:

^+1::Send        "❕"	;	   Ctrl-Shift-1 for ❕ [white]
!+1::Send        "❗"	;	    Alt-Shift-1 for ❗ [red]
^!+1::Send       "‼️"	;      Ctrl-Alt-Shift-1 for ‼️ [double red]
                 
+^!5::Send       "％"   ;     Ctrl+Alt+Shift-5 for ％  the cool percent (Ctrl+Alt+%)



;6                      ;                     6 for 6   ━━━ but some other arrows we could use are: ^ ↑ ⤊ ⇧ ⬆️ ⬆ ⤴ ▲   ↥ ⮝ ⏫ ⏶ △ 🔼 🆙 ⇑ ⟰
;+6                     ;               Shift+6 for ^
^+6::Send        "⬆️"    ;          Ctrl-Shift+6 for ⬆️
!+6::Send        "↑"    ;           Alt-Shift+6 for ↑
#+6::Send        "⇧"    ;           Win-Shift+6 for ⇧
^!#+6::Send      "⤊"    ;  Ctrl-Alt-Win-Shift+6 for ⤊
                                                       



;8                      ;                     8 for 8                
;* normal asterisk key  ;               Shift+8 for *  the normal asterisk key
^8::Send	 "⭐"    ;                Ctrl+8 for ⭐  big gold star [but looks tiny in EditPlus]
;!8::Send	 "★"    ;                 Alt+8 for ★  filled  black star but very small in browser                                  
!8::Send	 "⛧"    ;                 Alt+8 for ⛧  upside-down star [like a pentagram without the circle around it]
+!8::Send	 "✪"    ;           Shift-Alt+8 for ✪  inverse black star (^^^^^ same size as ^^^^^)
+^!8::Send	 "✨"   ;            Ctrl-Alt+8 for ✨ starry   star
;^!#8::Send      "🌟"   ;        Ctrl-Alt-Win+8 for 🌟 dramatic star

;9                      ;                     9 for 9
;+9                     ;               Shift+9 for (
;+9                     ;               Shift+0 for )
^+9::Send	 "❪"	;          Ctrl-Shift+9 for ❪ smaller parens
^+0::Send	 "❫"	;          Ctrl-Shift+9 for ❫ smaller parens
!+9::Send	 "⸨"	;           Alt-Shift+9 for ⸨ lower/smaller double parens
!+0::Send	 "⸩"	;           Alt-Shift+9 for ⸩ lower/smaller double parens
^!+9::Send	 "｟"	;      Ctrl-Alt-Shift+9 for   upper/bigger double parens
^!+0::Send	 "｠"	;      Ctrl-Alt-Shift+9 for   upper/bigger double parens
#+9::Send	 "﴾"	;       Windows-Shift+9 for   ornate parens
#+0::Send	 "﴿"	;       Windows-Shift+9 for   ornate parens
; others: ⦅⦆ ⦇⦈ ❨❩ ❪❫
                        
;-------         "-"    ;         Hyphen ------ for normal default hyphen                     (compound words, words interrupted by line break)
^-::Send         "–"    ;    Ctrl+Hyphen –––––– for en dash                                   (ranges,    quotations)
!-::Send         "—"    ;     Alt+Hyphen —————— for em dash                                   (interruptions, breaks)
^!-::Send        "━"    ;Ctrl-Alt+Hyphen ━━━━━━ for unicode box drawing heavy horizontal line (      dividers       )      
                      
;=::Send         "="    ;“=”         Equals key for the normal equals
;^=::Send        "═"    ;“═”    Ctrl-Equals key for the connecting_equals symbol but we have this disabled becuase it’s used for zoom up in Windows Terminal
;!=::Send        "═"    ;“═”     Alt-Equals key for the connecting_equals symbol aka box drawing horizontal double
!=::Send         "─"    ;“─”     Alt-Equals key for the unicode box drawing light horizontal      (      dividers       ) WHICH LOOKS SAME AS EMDASH BUT CONNECTS WITH OTHER DRAWING CHARS BETTER BECUASE IT’S SLIGHTLY HIGHER
^!=::Send        "═"    ;“═”Ctrl-Alt-Equals key for the connecting_equals symbol		      


;;;;; NUMBER KEYS:

#^!0::Send       "⓿"    ;        Win-Ctrl+Alt+0 for darkcircled number ⓿
#^!1::Send       "❶"    ;        Win-Ctrl+Alt+1 for darkcircled number ❶
#^!2::Send       "❷"    ;        Win-Ctrl+Alt+2 for darkcircled number ❷
#^!3::Send       "❸"    ;        Win-Ctrl+Alt+3 for darkcircled number ❸
#^!4::Send       "❹"    ;        Win-Ctrl+Alt+4 for darkcircled number ❹
#^!5::Send       "❺"    ;        Win-Ctrl+Alt+5 for darkcircled number ❺
#^!6::Send       "❻"    ;        Win-Ctrl+Alt+6 for darkcircled number ❻
#^!7::Send       "❼"    ;        Win-Ctrl+Alt+7 for darkcircled number ❼
#^!8::Send       "❽"    ;        Win-Ctrl+Alt+8 for darkcircled number ❽
#^!9::Send       "❾"    ;        Win-Ctrl+Alt+9 for darkcircled number ❾


;;;;; NUMPAD KEYS (NUMLOCK OFF):

^#NumPad0::Send  "⁰"    ;      Ctrl-Win-NumPad0 for superscript number ⁰
^#NumPad1::Send  "¹"    ;      Ctrl-Win-NumPad1 for superscript number ¹
^#NumPad2::Send  "²"    ;      Ctrl-Win-NumPad2 for superscript number ²
^#NumPad3::Send  "³"    ;      Ctrl-Win-NumPad3 for superscript number ³
^#NumPad4::Send  "⁴"    ;      Ctrl-Win-NumPad4 for superscript number ⁴
^#NumPad5::Send  "⁵"    ;      Ctrl-Win-NumPad5 for superscript number ⁵
^#NumPad6::Send  "⁶"    ;      Ctrl-Win-NumPad6 for superscript number ⁶
^#NumPad7::Send  "⁷"    ;      Ctrl-Win-NumPad7 for superscript number ⁷
^#NumPad8::Send  "⁸"    ;      Ctrl-Win-NumPad8 for superscript number ⁸
^#NumPad9::Send  "⁹"    ;      Ctrl-Win-NumPad9 for superscript number ⁹

#NumPad0::Send   "₀"    ;           Win-NumPad0 for   subscript number ₀
#NumPad1::Send   "₁"    ;           Win-NumPad1 for   subscript number ₁
#NumPad2::Send   "₂"    ;           Win-NumPad2 for   subscript number ₂
#NumPad3::Send   "₃"    ;           Win-NumPad3 for   subscript number ₃
#NumPad4::Send   "₄"    ;           Win-NumPad4 for   subscript number ₄
#NumPad5::Send   "₅"    ;           Win-NumPad5 for   subscript number ₅
#NumPad6::Send   "₆"    ;           Win-NumPad6 for   subscript number ₆
#NumPad7::Send   "₇"    ;           Win-NumPad7 for   subscript number ₇
#NumPad8::Send   "₈"    ;           Win-NumPad8 for   subscript number ₈
#NumPad9::Send   "₉"    ;           Win-NumPad9 for   subscript number ₉

!#NumPad0::Send  "⓪"    ;       Alt-Win-NumPad0 for opencircled number ⓪
!#NumPad1::Send  "①"    ;       Alt-Win-NumPad1 for opencircled number ①
!#NumPad2::Send  "②"    ;       Alt-Win-NumPad2 for opencircled number ②
!#NumPad3::Send  "③"    ;       Alt-Win-NumPad3 for opencircled number ③
!#NumPad4::Send  "④"    ;       Alt-Win-NumPad4 for opencircled number ④
!#NumPad5::Send  "⑤"    ;       Alt-Win-NumPad5 for opencircled number ⑤
!#NumPad6::Send  "⑥"    ;       Alt-Win-NumPad6 for opencircled number ⑥
!#NumPad7::Send  "⑦"    ;       Alt-Win-NumPad7 for opencircled number ⑦
!#NumPad8::Send  "⑧"    ;       Alt-Win-NumPad8 for opencircled number ⑧
!#NumPad9::Send  "⑨"    ;       Alt-Win-NumPad9 for opencircled number ⑨


;;;;; UPPER LETTERS ROW:

;                       ;               [ for [
;                       ;               ] for ]
;                       ;         Shift-[ for {
;                       ;         Shift-] for }
;                       ;           Win-[ for rewind  5 seconds in winamp
;                       ;           Win-] for advance 5 seconds in winamp
^#[::Send         "⟦"	;      Ctrl-Win-[ for cute
^#]::Send         "⟧"	;      Ctrl-Win-] for cute
!#[::Send	 "〚"	;       Alt-Win-[ for 2x with whitespace
!#]::Send	 "〛"	;       Alt-Win-] for 2x with whitespace
^!#[::Send	 "【"	;  Ctrl-Alt-Win-[ for dramatic
^!#]::Send	 "】"	;  Ctrl-Alt-Win-] for dramatic

;❶ 【】〚〛[normal［upper］brackets]⟦⟧  
;❷ [【dramatic】] [〚2× with whitespace〛] [⟦2× small⟧] [［up］]  ... ctrl, alt, ctrl-alt
;❸ [how does【this】 look?] [how about 〚a red〛 head] [how about a ⟦red⟧ head] [how about a ［red］ head]  
;❹ can’t really tell the upper. .. the 2xwWP are kind of annoying... .. the 2x small are cute
;maybe ctrl=cute, alt=2xwwh, ctrl-alt=drama


;TODO {} ﹛ctrl﹜ ⦃alt⦄ ｛ctrl-alt｝
;+[::Send        "{"    ;         Shift-[ for {
;+]::Send        "}"    ;         Shift-[ for }

		      
;|::Send         "|"    ; “|” —          Pipe key for “|” — the normal pipe
^|::Send         "│"    ; “│” —     Ctrl-Pipe key for “│” — the thin   connecting vertical bar
!|::Send         "┃"    ; “┃” —      Alt-Pipe key for “┃” — the thick  connecting vertical bar
^!|::Send        "║"    ; “║” — Ctrl-Alt-Pipe key for “║” — the double connecting vertical bar




;;;;; MIDDLE LETTERS ROW / HOME KEY ROW:

;;You know what we need? An enter on the left side of the keyboard. To truly become the Mistress of your own domain, if you know what I mean 😉😉😏
^CapsLock::Send "{Enter}"       ; Ctrl-Caps for a left-side-of-keyboard ENTER key
^`::Send        "{Enter}"       ; Ctrl-`    for a left-side-of-keyboard ENTER key that doesn’t hurt the hand as much when held for a long time


!'::Send  "{U+0027}"    ;      Alt+apostrophe for '  default original dumb apostrophe / feet symbol
'::Send   "’"           ;          apostrophe for ’  smart single quote: right           ; the *correct* apostrophe we should be using, i.e. “can’t”
^'::Send  "‘"           ;     Ctrl+apostrophe for ‘  smart single quote: left
^!'::Send "‘’"          ; Ctrl-Alt+apostrophe for ‘’ smart single quotes: both
		         
;"(normal quote key)    ;"          quote for "   — "the default original dumb quote / inches symbol"
^!"::Send "“”"          ;" Ctrl+Alt+quote for “”  — smart double/normal quotes: both
^"::Send  "“"           ;"     Ctrl+quote for “   — smart double/normal quotes: left
!"::Send  "”"           ;"      Alt+quote for ”   — smart double/normal quotes: right



;;;;; LOWER LETTERS ROW:
		      
;|::Send   "x"          ; “x”  —                x key for the normal x
;^|::Send  "│"		;      —           Ctrl-x key is definitely reserved for other things
;!|::Send  "┃"		;      —            Alt-x key is likely     reserved for other things
^!x::Send  "×"		; “×”  —       Ctrl-Alt-x key for “×” , the multiplication unicode symbol, which is more in the center than the “x” is:  ×x×x×x×x×
+^!X::Send "✖️"		; “✖️” — Shift-Ctrl-Alt-x key for “✖️”, the multiplication  emoji  symbol, which is huuuge compared to the x: x×X✖️


; ,::Send  "❟"		;          Comma for “❟” smart comma / fancy unicode comma [in editplus, it looks “dumber” (“❟”) than the “dumb” comma (“,”)
;^,::Send  "{U+2C}"	;     Ctrl-Comma for “,” dumb comma / original/normal comma but Windows Terminal overrides this
;!,::Send  "{U+2C}"	;      Alt-Comma for “,” dumb comma / original/normal comma
;^!,::Send "{U+2C}"	; Ctrl-Alt-Comma for “,” dumb comma / original/normal comma

;,::Send   ","          ;          Comma for “,” the normal comma key we’re all used —— the “dumb” comma / original comma / “normal” comma 
^,::Send   "❟"          ;     Ctrl-Comma for “,” smart comma /	fancy unicode comma —— but Windows Terminal overrides this
!,::Send   "❟"          ;      Alt-Comma for “❟”  smart comma /	fancy unicode comma [in editplus, it looks “dumber” (“❟”) than the “dumb” comma (“,”)
^!,::Send  "❟"          ; Ctrl-Alt-Comma for “❟”  smart comma /	fancy unicode comma [in editplus, it looks “dumber” (“❟”) than the “dumb” comma (“,”)
		      
;TODO?     ⟪double⟫    thin: ❰thin bold❱  ‹thin faint›  ❬thin small❭    
;>              be nice if ━> could somehow be a triangle to make a good arrow      

;;;;; SLASH / QUESTION MARK KEY:
;/::Send         "/"    ;                             / for /
;+/::Send        "?"    ;                       Shift-/ for ?
#/::Send         "÷"    ;                         Win-/ for ÷  division symbol
^!#/::Send       "➗"  ;                Ctrl-Alt-Win-/ for ➗ division emoji
^/::Send         "⁄"    ;                        Ctrl-/ for ⁄  magical combiner slash that turns 5⁄8 into a 5/8ths symbol in browsers and proper full implementation [but not in EditPlus or Windows Terminal]
^!/::Send        "⫽"   ;                    Ctrl-Alt-/ for ⫽  double slash
#!/::Send        "⫻"   ;                     Win-Alt-/ for ⫻  triple slash
^?::Send        "❔"    ;     Ctrl-? /     Ctrl-Shift-/ for ❔ [white]
!?::Send        "❓"    ;      Alt-? /      Alt-Shift-/ for ❓ [red]
^!?::Send       "⁉️"     ; Ctrl-Alt-? / Ctrl-Alt-Shift-/ for ⁉️ 

;                                 3-chars-wide in browser
;                   3-lines-hi in browser          overlaps in tcc
;            8275         8260             overlaps in TCC
;            ⁄fract       MAGICAL COMBINER in browser, verrrrry slanted in tcc
;     /norm  ∕div         ⁄fract                    
;     /      ∕      ⧸     ⁄         ／     ⫽     ⫻     ÷ ➗
;½  [1/2]  [1∕2]  [1⧸2] [1⁄2]     [1／2] [1⫽2] [1⫻2]   ÷ ➗
;ocr double backslash, it’s so tiny>⑊
;  Magic combiner gives control of making characters, use as Ctrl-Slash .. 
; double-slash could be Ctrl-Alt-slash  and triple-slash could be Win-Alt-slash⫻
; win-slash? ÷    Ctrl-Alt-Win-Slash ➗

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; KEYBOARD ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;














;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; CAPS/NUM/SCROLL LOCK/INSERT POP-UPS / STATE-TRACKING ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

#Include c:\bat\ToolTipOptions.ahk
Persistent

;;;;; SET INITIAL STATE FOR TRACKED KEYS:
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
global      insert_mode         := 0  
global    num_lock_mode         := 0
global   caps_lock_mode         := 0
global scroll_lock_mode         := 0
global       dummy_mode         := 0  ;used to avoid passing caps lock mode because we manage that in the outer layer, but the other 2 in the inner layer
          
;;;;; DEFINE TRAYTEXT CONTENTS: -- TODO 🐐 finish the large renderings of the other ones haha

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

;;;;; REMAP THE KEYS TO CALL TRAYTEXT FUNCTION WITH PROPER TRAYTEXT:
Insert::   
{ 
    Send      "{Insert}"  
    HandleKey( "Insert"   ,      "insert_mode",     insert_up_tray_text,     insert_dn_tray_text,     insert_up_popup_text,     insert_dn_popup_text,               "[2 q",               "[4 q") 
}
NumLock:: 
{ 
    if (GetKeyState(   "NumLock", "T")) {
        SetNumLockState("Off")          ; Turn Num Lock Off
    } else {                                                   
        SetNumLockState( "On")          ; Turn Num Lock On
    }
    HandleKey( "NumLock"  ,    "num_lock_mode",    numLock_up_tray_text,    numLock_dn_tray_text,    numLock_up_popup_text,    numLock_dn_popup_text,              "dummy",              "dummy") 
}
CapsLock:: 
{ 
    if (GetKeyState(  "CapsLock", "T")) {
        SetCapsLockState("Off")         ; Turn Caps Lock Off
    } else {                                                   
        SetCapsLockState( "On")         ; Turn Caps Lock On
    }
    HandleKey( "CapsLock" ,   "caps_lock_mode",   capsLock_up_tray_text,   capsLock_dn_tray_text,   capsLock_up_popup_text,   capsLock_dn_popup_text,              "dummy",              "dummy") 
}
ScrollLock:: 
{ 
    if (GetKeyState("ScrollLock", "T")) {
        SetScrollLockState("Off")       ; Turn Scroll Lock Off
    } else {                                                   
        SetScrollLockState( "On")       ; Turn Scroll Lock On
    }
    HandleKey("ScrollLock", "scroll_lock_mode", scrollLock_up_tray_text, scrollLock_dn_tray_text, scrollLock_up_popup_text, scrollLock_dn_popup_text,              "dummy",              "dummy") 
}

;;;;; FUNCTION TO KEEP TRACK OF KEYS AND GENERATE TRAYTEXT:
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
    ToolTipOptions.SetTitle(     " ", 4     )                            ; makes a blue exclaimation mark on the pop-up box to the left of our text
    ToolTipOptions.SetColors("White", "Blue")
    ToolTip popup_text, A_ScreenWidth //2 - x_offset, A_ScreenHeight//2 - y_offset
    SetTimer(() => ToolTip("", 0), 750)                                  ; hide the on-screen banner  after these many ms

    CoordMode "ToolTip", "Screen"
    TrayTip   "⚠`n"   tray_text   
    SetTimer () =>TrayTip(), -1000                                       ; hide the tray notificatiOn after these many ms
    return
}
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; CAPS/NUM/SCROLL LOCK/INSERT POP-UPS;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;






;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; WINAMP ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 🌟🌟🌟 NOT WORKING WELL!! 🌟🌟🌟


WinampClass := "ahk_class Winamp v1.x"                                  ; Define the Winamp window class

;; Activate Winamp window —— I set Ctrl-Alt-W in Windows internal hotkeys (2025)
#w::MinimizeOrRaiseWinamp()
^!w::MinimizeOrRaiseWinamp()

;; ⏸⏯ Pause ⏸⏯ 
Pause::SendWinampPause()
^!p::SendWinampPause()
#c::SendWinampPause()
F9::SendWinampPause()                                                   ; 20250527: TODO remove F9 after we sit with it for awhile for testing purposes
       
;; ⏹⏹ Stop ⏹⏹                                                 
^!v::PostMessage(       0x111, 40047, 0, , WinampClass  )               ; Stop
#v::PostMessage(        0x111, 40047, 0, , WinampClass  )
Media_Stop::PostMessage(0x111, 40047, 0, , WinampClass  )
                   
;; ⏭⏭ Next ⏭⏭                                     
^!b::PostMessage(       0x111, 40048, 0, , WinampClass  )               ; Next Track
#b::PostMessage(        0x111, 40048, 0, , WinampClass  )
Media_Next::PostMessage(0x111, 40048, 0, , WinampClass  )
                 
;; ⏮⏮ Previous ⏮⏮                                       
^!z::PostMessage(       0x111, 40044, 0, , WinampClass  )               ; Previous Track
#z::PostMessage(        0x111, 40044, 0, , WinampClass  )
Media_Prev::PostMessage(0x111, 40044, 0, , WinampClass  )
                                                        

SendWinampPause() {
        SendRawCToWinamp()
}
SendRawCToWinamp() {
    hwnd := WinExist("ahk_class Winamp v1.x")
    if !hwnd
        return

    VK_C       := 0x43                                                  ; Virtual-Key code for “C”
    SC_C       := 0x2E
    WM_KEYDOWN := 0x0100                                                ; Send WM_KEYDOWN and WM_KEYUP
    WM_KEYUP   := 0x0101

    PostMessage(WM_KEYDOWN, VK_C,  SC_C << 16              , , hwnd)    ; Send key press to the main window
    Sleep 20
    PostMessage(WM_KEYUP  , VK_C, (SC_C << 16) | 0xC0000000, , hwnd)
}


MinimizeOrRaiseWinamp() {
    hwnd := WinExist("ahk_class Winamp v1.x")
    if !hwnd
        return

    ourWinGetMinMax := WinGetMinMax(hwnd)
    if ourWinGetMinMax == -1 {
        WinRestore(hwnd)
    } else {
        WinMinimize(hwnd)
    }
}

F8::ShowWinampState()                                                   ; TODO 20250527 remove this after testing
ShowWinampState() {
    hwnd := WinExist("ahk_class Winamp v1.x")
    if !hwnd
        return

    WM_USER       := 0x400
    IPC_ISPLAYING := 104
    result        := SendMessage(WM_USER + IPC_ISPLAYING, 0, 0, , hwnd)

    ToolTip("Winamp state: " . result . " (Type: " . Type(result) . ")")
}

;;    SendWinampPause_NO() {
;;        hwnd := WinExist("ahk_class Winamp v1.x")
;;        if !hwnd
;;            return
;;    
;;        WM_USER := 0x400
;;        IPC_ISPLAYING := 104
;;        WM_COMMAND := 0x111
;;        CMD_PLAYPAUSE := 40045
;;    
;;        ; Ask Winamp what state it's in (0=stopped, 1=playing, 3=paused)
;;        state := SendMessage(WM_USER + IPC_ISPLAYING, 0, 0, , hwnd)
;;    
;;        if (state == 1 || state == 3) {
;;            ; Only send Play/Pause if currently playing or paused
;;            PostMessage(WM_COMMAND, CMD_PLAYPAUSE, 0, , hwnd)
;;            ToolTip("Play/Pause sent to Winamp")
;;            SetTimer(() => ToolTip(), -1000)
;;        } else {
;;            ToolTip("Winamp is stopped – not pausing - state is")
;;            SetTimer(() => ToolTip(), -1000)
;;            ToolTip(state)
;;        }
;;    }
;;    
;;    SendWinampPauseUGH() {
;;        hwnd := WinExist("ahk_class Winamp v1.x")
;;        if hwnd {
;;            WM_USER := 0x400
;;            IPC_PAUSE := 100
;;            SendMessage(WM_USER + IPC_PAUSE, 0, 0, , hwnd)
;;            PostMessage(WM_USER + IPC_PAUSE, 0, 0, , hwnd)
;;            ToolTip("Pause sent to Winamp", 10, 10)
;;            SetTimer(() => ToolTip(), -1000)  ; Clear tooltip after 1s
;;        }
;;    }




;;202505 REPLACED THIS: ;;; ; Stop, Windows-v, and Ctrl-Alt-V
;;202505 REPLACED THIS: ;; #IfWinExist %WinampClass%
;;202505 REPLACED THIS: ;; {
;;202505 REPLACED THIS: ;;     Media_Stop::
;;202505 REPLACED THIS: ;;     #v::
;;202505 REPLACED THIS: ;;     ^!v::
;;202505 REPLACED THIS: ;;     ControlSend, ahk_parent, v
;;202505 REPLACED THIS: ;;     return
;;202505 REPLACED THIS: ;; }
;;202505 REPLACED THIS: ;; 
;;202505 REPLACED THIS: ;; ; Next Track, Windows-b, and Ctrl-Alt-B
;;202505 REPLACED THIS: ;; #IfWinExist %WinampClass%
;;202505 REPLACED THIS: ;; {
;;202505 REPLACED THIS: ;;     Media_Next::
;;202505 REPLACED THIS: ;;     #b::
;;202505 REPLACED THIS: ;;     ^!b::PP 
;;202505 REPLACED THIS: ;;     ControlSend, ahk_parent, b
;;202505 REPLACED THIS: ;;     return
;;202505 REPLACED THIS: ;; }
;;202505 REPLACED THIS: ;; 
;;202505 REPLACED THIS: ;; ; Previous Track, Windows-z, and Ctrl-Alt-Z
;;202505 REPLACED THIS: ;; #IfWinExist %WinampClass%
;;202505 REPLACED THIS: ;; {
;;202505 REPLACED THIS: ;;     Media_Prev::
;;202505 REPLACED THIS: ;;     #z::
;;202505 REPLACED THIS: ;;     ^!z::
;;202505 REPLACED THIS: ;;     ControlSend, ahk_parent, z
;;202505 REPLACED THIS: ;;     return
;;202505 REPLACED THIS: ;; }
;;202505 REPLACED THIS: 
;;202505 REPLACED THIS: ;;Winamp v1.x
;;202505 REPLACED THIS: ^!p::
;;202505 REPLACED THIS: Pause::
;;202505 REPLACED THIS: #C::
;;202505 REPLACED THIS: {
;;202505 REPLACED THIS:     if not WinExist("ahk_class Winamp v1.x")
;;202505 REPLACED THIS:         return           ; Otherwise, the above has set the "last found" window for use below.
;;202505 REPLACED THIS:         ControlSend "c"  ; Pause/Unpause
;;202505 REPLACED THIS: }
;;202505 REPLACED THIS: 
;;202505 REPLACED THIS: #W:: {
;;202505 REPLACED THIS:   WinActivate("*Winamp*")
;;202505 REPLACED THIS: }
;;202505 REPLACED THIS: 
;;202505 REPLACED THIS: ;;     Pause::
;;202505 REPLACED THIS: ;;     #c::
;;202505 REPLACED THIS: ;;     ^!c::
;;202505 REPLACED THIS: ;;     ControlSend, ahk_parent, c
;;202505 REPLACED THIS: ;;     return
;;202505 REPLACED THIS: ;; }
;;202505 REPLACED THIS: ;; 

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; WINAMP ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
