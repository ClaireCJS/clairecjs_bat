@on break cancel
@echo off
call advice "USAGE: join-videos *.avi"
pause
set target=c:\output
mencoder -oac pcm -ovc copy -o %target% %*
echos %target%>clip:
call important "saved to “%ITALICS_ON%%target%%ITALICS_OFF%”"
