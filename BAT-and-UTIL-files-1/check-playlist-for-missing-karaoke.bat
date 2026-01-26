@loadbtm on
@Echo OFF

iff "%1" eq "" then
        call warning "Must provide a playlist name to check for missing karaoke/subtitles from!" silent
else
        @call check-for-missing-karaoke.bat %1
endiff        