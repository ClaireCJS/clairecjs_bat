@Echo OFF
 on break cancel

call validate-in-path youtube-dl important pause wait echo mv advice
call validate-environment-variables UTIL color_important


%UTIL%


call important Take note of the current version:
youtube-dl.exe --version
pause

call important Attempting youtube-dl upgrade
youtube-dl.exe -U
call wait 3
echo yryryr|mv youtube-dl.exe.new youtube-dl.exe

%COLOR_IMPORTANT%
call important Let's check the version to see if it upgraded...
youtube-dl.exe --version

call advice "If that didn't didn't work, you might have installed youtube-dl via python in which case you need to do a %italics_on%pip%italics_off% upgrade"
