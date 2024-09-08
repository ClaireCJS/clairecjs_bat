@Echo OFF

:DESCRIPTION: Rolls the logfile from the MadVR renderer into c:\logs\ where it should belong

set        TARGET=%USERPROFILE%\Desktop\madVR - log.txt
if exist "%TARGET%" (echo ray|copy "%TARGET" c:\logs\)
