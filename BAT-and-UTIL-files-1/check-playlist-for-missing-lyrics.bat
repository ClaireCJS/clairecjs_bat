@Echo OFF

iff "%1" eq "" then
        call warning "Must provide a playlist name to check for missing lyrics from!" silent
else
        @call check-for-missing-lyrics.bat %1
endiff        