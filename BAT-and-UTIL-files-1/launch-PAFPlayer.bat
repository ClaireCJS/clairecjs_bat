@Echo off


              set PAFPLAYER_LAUNCH_ARGS=resume
if "%1" != "" set PAFPLAYER_LAUNCH_ARGS=%*

rem start /elevated /max wt -w 0 c:\tcmd\tcc.exe %UTIL%\PAFplayer\pafplayer.bat %PAFPLAYER_LAUNCH_ARGS%
    start /elevated /max wt --pos -1920,0      c:\tcmd\tcc.exe %UTIL%\PAFplayer\pafplayer.bat %PAFPLAYER_LAUNCH_ARGS%

