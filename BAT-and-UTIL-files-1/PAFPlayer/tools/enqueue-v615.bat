@on break cancel

iff "%MUSIC_PLAYER%" == "WINAMP" then
        call enqueue-file-into-winamp-playlist.bat %*
elseiff "%MUSIC_PLAYER%" == "PAFPLAYER" then
        call PAFPlayer --enqueue %*
else
        call error "MUSIC_PLAYER must be defined"
endiff
