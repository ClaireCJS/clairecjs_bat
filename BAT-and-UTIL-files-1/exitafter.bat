@on break cancel
@Echo OFF


:DESCRIPTION: This simply issues an 'exit' command if we are passed 'exit' or 'exitafter' for either %1 or %2

:USAGE: At the end of any bat file, simply invoke: call exitafter %* —— This will exit if the proper parameters or environment variables were set

if "%1" eq  "exit"      (exit)
if "%2" eq  "exit"      (exit)
if "%1" eq  "exitafter" (exit)
if "%2" eq  "exitafter" (exit)
if  "1" eq "%EXITAFTER" (set EXITAFTER=0 %+ exit)

