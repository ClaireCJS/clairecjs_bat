@Echo off
@on break cancel

:DESCRIPTION: runs the *PIPED INPUT* as a bat file

if  not  isdir %temp% (call fatal_error "temp folder %temp% doesn't exist")
set   tempfile=%temp%\tempfile-runasbat-%_utcdatetime-%_pid-%@random[0,999999].bat
type    >:u8  "%tempfile%"
if not exist  "%tempfile%"       goto :NeverMind
if %@FILESIZE["%tempfile%"] eq 0 goto :NeverMind
call          "%tempfile%"
rem (*del    /q   "%tempfile%")      >&>nul

:NeverMind

