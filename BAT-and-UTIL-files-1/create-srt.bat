@Echo OFF

rem Some trickery in case we call create-srt ai thinking it was create-srt-for-currently-playing-song but really it's create-srt-from-file
rem "%1" eq "ai" .or. "%1" eq "force" then
iff "%1" eq "current" then
        create-lrc-file-for-currently-playing-song.bat
else
        @call create-lrc-from-file.bat %*
endiff