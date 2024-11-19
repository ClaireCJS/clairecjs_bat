@echo off
@on break cancel
call switch-winamp-to-playlist.bat %*
call less_important "echo Waiting 2 seconds before randomizing"
call sleep 2
%COLOR_RUN%       
call winamp-playlist-randomize.bat %*

if "%1"=="nonext" .OR. "%2"=="nonext" .OR. "%3"=="nonext" .OR. "%4"=="nonext" .OR. "%NEXT%"=="0" goto :Next_No
if "%1"==  "next" .OR. "%2"==  "next" .OR. "%3"==  "next" .OR. "%4"==  "next" .OR. "%NEXT%"=="1" goto :Next_Yes
	:Next_Default
	:Next_No
		goto :END
	:Next_Yes
		call next.bat %*
		goto :END
:END

