@Echo OFF
@on break cancel

:DESCRIPTION: Copies the logfile from the MadVR renderer into c:\logs\ with the rest of our logfiles

set        TARGET=%USERPROFILE%\Desktop\madVR - log.txt
if exist "%TARGET%" (echo ray|copy "%TARGET" c:\logs\)
