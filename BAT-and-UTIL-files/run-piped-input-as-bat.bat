@echo off

:DESCRIPTION: runs the *PIPED INPUT* as a bat file


set    tempfile=%temp%\tempfile-runasbat-%_utcdatetime.bat
type>"%tempfile%"
call "%tempfile%"
del  "%tempfile%"

