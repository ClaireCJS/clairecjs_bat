@Echo OFF

if     %WINAMP_CLOSE_GRACEFULLY_VALIDATED ne 1 (
    set WINAMP_CLOSE_GRACEFULLY_VALIDATED=1
    call validate-environment-variables UTIL2 MUSICSERVERIPONLY GIRDERPORT GIRDERPASSWORD 
)

call subtle "Attempting to close WinAmp with WinAmp" %+ "%UTIL2%\winamp repo\winamp\winamp.exe" /kill
call subtle "Attempting to close WinAmp with Girder" %+ girder-internet-event-client %MUSICSERVERIPONLY %GIRDERPORT %GIRDERPASSWORD DIE_WINAMP whatever

