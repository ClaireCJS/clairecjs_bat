@Echo off


              set PAFPLAYER_LAUNCH_ARGS=resume
if "%1" != "" set PAFPLAYER_LAUNCH_ARGS=%*

wt tcc c:\bat\pafplayer.bat %PAFPLAYER_LAUNCH_ARGS%



