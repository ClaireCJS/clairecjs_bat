@Echo Off


rem Validate environment:
        iff "2" != "%validated_getlrc%" then
                call validate-in-path get-lyrics-for-file.btm
                set validated_getlrc=2
        endiff


rem Get parameter:
        set FILE=%@UNQUOTE["%1"]


rem Pass to get-lyrics in “quick LRC” mode:
        call get-lyrics-for-file.btm "%FILE%" quick_lrc %2$



