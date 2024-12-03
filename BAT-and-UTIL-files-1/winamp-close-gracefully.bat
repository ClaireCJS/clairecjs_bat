@Echo OFF
 on break cancel
 
set WINAMP="%UTIL2%\winamp repo\winamp\winamp.exe"

if     %WINAMP_CLOSE_GRACEFULLY_VALIDATED ne 1 (
    set WINAMP_CLOSE_GRACEFULLY_VALIDATED=1
    call validate-environment-variables UTIL2 MUSICSERVERIPONLY GIRDERPORT GIRDERPASSWORD WINAMP
    call validate-in-path girder-internet-event-client
)

echos %ANSI_COLOR_LOGGING%


call subtle "Attempting to close WinAmp with WinAmp" %+ %WINAMP% /kill
call subtle "Attempting to close WinAmp with Girder" %+ girder-internet-event-client %MUSICSERVERIPONLY %GIRDERPORT %GIRDERPASSWORD DIE_WINAMP whatever

