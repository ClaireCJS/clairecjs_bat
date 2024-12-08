@Echo OFF
@on break cancel



set VERBOSITY=%DEBUG%                                %+ REM 0=silent, 1=announce conclusion



set PURPOSE=
if "%1" ne "" (set PURPOSE=.%1)

set TEMP_FOLDER=temp.%_utcdatetime%%PURPOSE%.%_PID%

if %VERBOSITY% GT 0 (call important_less "TEMP_FOLDER set to “%TEMP_FOLDER%”")
