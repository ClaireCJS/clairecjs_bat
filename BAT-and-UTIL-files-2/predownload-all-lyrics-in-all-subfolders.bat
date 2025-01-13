@loadbtm on
@Echo OFF

pushd .

call validate-in-path predownload-lyrics-here sweep-random status-bar


pause /# 10 "Make sure you’re in the root folder of your audio before running this!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"

if "%@alias[UNKNOWN_CMD]" != "" unalias UNKNOWN_CMD

set PREDOWNLOADED_LYRICS_JUST_NOW=0

call sweep-random "call predownload-lyrics-here" force


if exist c:\bat\realias.bat call c:\bat\realias.bat

call status-bar unlock


popd 

echo PREDOWNLOADED_FOLDERS_JUST_NOW is %PREDOWNLOADED_FOLDERS_JUST_NOW
set SorNot=%@IF[%PREDOWNLOADED_FOLDERS_JUST_NOW gt 1,s,]
set PorNot=%@IF[%PREDOWNLOADED_FOLDERS_JUST_NOW gt 0,),]
call celebration "All done predownloading lyrics! %@IF[%PREDOWNLOADED_FOLDERS_JUST_NOW% gt 0,%faint_on%(processed %PREDOWNLOADED_FOLDERS_JUST_NOW% folder%SOrNot%%PorNot%%faint_off%,]"



