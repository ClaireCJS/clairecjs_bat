@Echo OFF
 on error cancel
 
rem   CDISPLAY="%ProgramFiles\CDisplay\CDisplay.exe"
set   CDISPLAY="%UTIL%\CDisplay\CDisplay.exe"
call  validate-environment-variable CDISPLAY "Must install cDisplay.exe to %CDISPLAY%"
start %@SFN[%CDISPLAY%] %*

