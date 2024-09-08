#SingleInstance

;;;;;;;; 
;;;;;;;;  2024 — What this does so far:
;;;;;;;; 
;;;;;;;;   *  Ctrl+Hyphen for en dash ––
;;;;;;;;   *   Alt+Hyphen for em dash ——
;;;;;;;; 
;;;;;;;;   *  NOT WORKING AS OF 20240426 — Pause Winamp — Pause key, Ctrl-Shift-P      
;;;;;;;;   *  NOT WORKING AS OF 20240426 — Show  Winamp — Windows-W
;;;;;;;;
;;;;;;;; 


;; ; Stop, Windows-v, and Ctrl-Alt-V
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
  WinActivate("Winamp")
}


^?::Send "❔" ; Ctrl+? for ❔ [white]
!?::Send "❓" ;  Alt+? for ❓ [red]
^8::Send "⭐" ; Ctrl+8 for ⭐
!8::Send "🌟" ;  Alt+8 for 🌟
^-::Send "–" ; Ctrl+Hyphen for en dash 
!-::Send "—" ;  Alt+Hyphen for em dash
















;;     Pause::
;;     #c::
;;     ^!c::
;;     ControlSend, ahk_parent, c
;;     return
;; }
;; 
