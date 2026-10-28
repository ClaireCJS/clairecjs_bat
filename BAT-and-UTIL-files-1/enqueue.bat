@Echo OFF
@on break cancel

iff "%MUSIC_PLAYER%" == "WINAMP" then
        call enqueue-file-into-winamp-playlist.bat %*
elseiff "%MUSIC_PLAYER%" == "PAFPLAYER" then
        @echo on
        call PAFPlayer --q %*
        @echo off
else
        call error "%italics_on%MUSIC_PLAYER%italics_off% must be defined"
endiff
