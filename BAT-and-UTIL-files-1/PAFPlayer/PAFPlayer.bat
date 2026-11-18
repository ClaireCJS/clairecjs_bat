@echo off
set args=%*
echo %ansi_color_less_important%%star2% Running PAFPlayer via the PAFPlayer\PAFPlayer.bat internal runtime launcher with args %args%%ansi_color_normal%
set "PAF_ROOT=%~dp0"
if exist "%PAF_ROOT%runtime\python.exe" (
  "%PAF_ROOT%runtime\python.exe" -B "%PAF_ROOT%PAFPlayer.py" %args%
) else (
  py -3 "%PAF_ROOT%PAFPlayer.py" %args%
)
rem exit /b %errorlevel%
