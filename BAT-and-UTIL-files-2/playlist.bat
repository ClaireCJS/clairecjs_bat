@echo off
@on break cancel


rem Validate environment (once):
        iff "1" != "%VALIDATED_PLAYLIST_BAT%" then
                rem Validate environment variables/ANSI:
                        if "1" != "%ANSI_COLORS_HAVE_BEEN_SET%" call validate-environment-variable ANSI_COLORS_HAVE_BEEN_SET

                rem Validate scripts/utilities we may call:
                        call validate-in-path print-message important less_important 
                        iff     "%MUSIC_PLAYER%" == "WINAMP"    then
                                call validate-in-path switch-winamp-to-playlist.bat
                        elseiff "%MUSIC_PLAYER%" == "PAFPlayer" then
                                call validate-in-path PAFPlayer.bat
                        endiff

                rem Store that we have validated things:
                        set VALIDATED_PLAYLIST_BAT=1
        endiff


rem Validate parameters:
        set PLAYLIST_TO_USE=%@UNQUOTE[%1]
        if not exist "%PLAYLIST_TO_USE%" call validate-environment-variable PLAYLIST_TO_USE


rem Preamble:
        call important "Switching to playlist %italics_on%%PLAYLIST_TO_USE%%italics_off%"


rem Actually switch to the playlist:
        iff "%MUSIC_PLAYER%" == "WINAMP" then
                call switch-winamp-to-playlist.bat %PLAYLIST_TO_USE%
                call less_important "echo Waiting 2 seconds before randomizing"
                call sleep 2
                call winamp-playlist-randomize.bat %*
                if  "%1"=="nonext" .OR. "%2"=="nonext" .OR. "%3"=="nonext" .OR. "%4"=="nonext" .OR. "%NEXT%"=="0" goto :Next_No
                iff "%1"==  "next" .OR. "%2"==  "next" .OR. "%3"==  "next" .OR. "%4"==  "next" .OR. "%NEXT%"=="1" then
                                call next.bat %*
                endiff
                :Next_No
                goto :END
        elseiff "%MUSIC_PLAYER%" == "PAFPlayer" then
                call PAFPlayer.bat                 %PLAYLIST_TO_USE%
                call PAFPlayer.bat                 randomize
        endiff



:END

