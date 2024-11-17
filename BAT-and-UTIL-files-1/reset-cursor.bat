@Echo OFF

iff defined CURSOR_RESET then
        echos %CURSOR_RESET%
else
        rem Don't think this works actually...
        echos %@CHAR[27][ q
        echos %@CHAR[27][ q
        echos %@CHAR[27]]12;#FF0000%
        echos %@CHAR[27][1 q
endiff