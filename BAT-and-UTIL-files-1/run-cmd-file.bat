@echo off
call validate-in-path cmd.exe
set FILE=%1
cmd.exe /c %FILE%

rem CMD [/A | /U] [/Q] [/D] [/E:ON | /E:OFF] [/F:ON | /F:OFF] [/V:ON | /V:OFF]
rem     [[/S] [/C | /K] string]
rem 
rem Starts a new instance of the Windows command interpreter
rem 
rem /C      Carries out the command specified by string and then terminates
rem /K      Carries out the command specified by string but remains
rem /S      Modifies the treatment of string after /C or /K (see below)
rem /Q      Turns echo off
rem /D      Disable execution of AutoRun commands from registry (see below)
rem /A      Causes the output of internal commands to a pipe or file to be ANSI
rem /U      Causes the output of internal commands to a pipe or file to be
rem         Unicode
rem /T:fg   Sets the foreground/background colors (see COLOR /? for more info)
rem /E:ON   Enable command extensions (see below)
rem /E:OFF  Disable command extensions (see below)
rem /F:ON   Enable file and directory name completion characters (see below)
rem /F:OFF  Disable file and directory name completion characters (see below)
rem /V:ON   Enable delayed environment variable expansion using ! as the
rem         delimiter. For example, /V:ON would allow !var! to expand the
rem         variable var at execution time.  The var syntax expands variables
rem         at input time, which is quite a different thing when inside of a FOR
rem         loop.
rem /V:OFF  Disable delayed environment expansion.
