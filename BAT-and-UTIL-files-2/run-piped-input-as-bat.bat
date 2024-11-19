@Echo off
@on break cancel

:DESCRIPTION: runs the *PIPED INPUT* as a bat file

if  not  isdir %temp% (call fatal_error "temp folder %temp% doesn't exist")
set   tempfile=%temp%\tempfile-runasbat-%_utcdatetime.bat
type    >:u8  "%tempfile%"
if not exist  "%tempfile%"       goto :NeverMind
if %@FILESIZE["%tempfile%"] eq 0 goto :NeverMind
call          "%tempfile%"
(del    /q    "%tempfile%")      >&>nul

:NeverMind

