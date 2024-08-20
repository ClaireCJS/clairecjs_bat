@Echo Off

taskend /f lastfm*
set                                  LAST_FM_LOGDIR=%LOGS%\Last.FM
call ensure-directories-exist       %LAST_FM_LOGDIR %LOGS% 
call validate-environment-variables  LAST_FM_LOGDIR AUDIOSCROBBLER_LOG
call yyyymmddhhmmss.bat
set target=%LAST_FM_LOGDIR%\LastFM-%MUSICSERVERMACHINENAME%-upto-%YYYYMMDDHHMMSS.log
echo ray|*move /r /q "%AUDIOSCROBBLER_LOG%" "%TARGET%"
if exist %TARGET% (echos %TAB% %+ call unimportant "Last.FM log backed up")
call start-lastfm

