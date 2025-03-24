@Echo Off
@on break cancel

iff "%MACHINENAME%" ne "%MUSICSERVERMACHINENAME%" then
        call warning_soft "No last.fm log to backup because this machine is not %italics_on%%MUSICSERVERMACHINENAME%%italics_off%"
        goto :END
endiff

call yyyymmddhhmmss.bat

taskend /f lastfm*
set                                 LAST_FM_LOGDIR=%LOGS%\Last.FM
call      ensure-directories-exist %LAST_FM_LOGDIR %LOGS% 
set                         target=%LAST_FM_LOGDIR%\LastFM-%MUSICSERVERMACHINENAME%-upto-%YYYYMMDDHHMMSS.log
call validate-environment-variables LAST_FM_LOGDIR AUDIOSCROBBLER_LOG
call validate-in-path yyyymmddhhmmss unimportant 


echo ray | *move /r /q "%AUDIOSCROBBLER_LOG%" "%TARGET%" >&>nul

iff exist %TARGET% then
        call less_important "Last.FM log rolled into: %ansi_color_important%%italics_on%%target%%italics_off%%ansi_color_subtle"
endiff



:END