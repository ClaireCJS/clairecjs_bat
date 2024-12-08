@Echo OFF
@on break cancel
set               RAR_PARAMS_BAT=%*
set               RAR="c:\Program Files\WinRAR\Rar.exe"
if   not exist   %RAR% (call fatal_error "RAR var set to something that does not exist: “%RAR%”")
set         REDOCOMMAND=%RAR%  %RAR_PARAMS_BAT%
rem @echo on
           %REDOCOMMAND%
rem @echo off
