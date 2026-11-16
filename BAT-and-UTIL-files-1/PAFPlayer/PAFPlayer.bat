@echo off
call less_important "Running PAFPlayer via the PAFPlayer\PAFPlayer.bat internal runtime launcher"
setlocal
set "PAF_ROOT=%~dp0"
if exist "%PAF_ROOT%runtime\python.exe" (
  "%PAF_ROOT%runtime\python.exe" -B "%PAF_ROOT%PAFPlayer.py" %*
) else (
  py -3 "%PAF_ROOT%PAFPlayer.py" %*
)
rem exit /b %errorlevel%
