@Echo Off
 on break cancel
@REM turning echo on is a great way to debug development of new ones

setdos /X0
call bigecho "%ANSI_COLOR_DEBUG%allfiles helper"
%COLOR_DEBUG%   %+ echo * allfiles-helper.bat (run-then-delete: %2)
%COLOR_NORMAL%  %+ cd      "%1"
%COLOR_NORMAL%  %+ call    "%2" %3*
:COLOR_DEBUG%   %+ echo if not exist "%@UNQUOTE[c:\recycled\%@NAME[%2]]" (move /r "%@UNQUOTE[%2]" c:\recycled)
%COLOR_REMOVAL% %+      if not exist "%@UNQUOTE[c:\recycled\%@NAME[%2]]" (move /r "%@UNQUOTE[%2]" c:\recycled)
%COLOR_NORMAL% 

if "%SWEEPING%" eq "1" goto :NoCLS
if "%NOCLS%"    eq "1" goto :NoCLS

    cls

:NoCLS

