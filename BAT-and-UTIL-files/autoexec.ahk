#SingleInstance

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
;;     ^!b::
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


#C::
Pause::
^!p::
{
    if not WinExist("ahk_class Winamp v1.x")
        return
    ; Otherwise, the above has set the "last found" window for use below.
        ControlSend "c"  ; Pause/Unpause
}


#W:: {
  WinActivate("Winamp")
}
















;;     Pause::
;;     #c::
;;     ^!c::
;;     ControlSend, ahk_parent, c
;;     return
;; }
;; 
