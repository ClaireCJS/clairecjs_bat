@Echo Off

pushd .

call validate-in-path predownload-lyrics-here sweep-random status-bar

if "%@alias[UNKNOWN_CMD]" ne "" unalias UNKNOWN_CMD

pause /# 10 "Make sure you’re in the root folder of your audio before running this!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"

call sweep-random "call predownload-lyrics-here" force

call status-bar unlock

if exist c:\bat\realias.bat call c:\bat\realias.bat

popd 



