@Echo OFF


iff "%1" == "" then
                    call get-lyrics-for-currently-playing-song %*
else
                    call get-lyrics-for-song %*
endiff

