@loadbtm on
@Echo Off
@on break cancel

rem Validate environment (once):
        iff "1" != "%validated_getlrc%" then
                call validate-in-path get-lyrics-for-file.btm validate-environment-variable
                set validated_getlrc=1
        endiff

rem Get parameter:
        set FILE=%@UNQUOTE["%1"]

rem Validate parameter:
        if not exist FILE (call validate-environment-variable FILE "1ˢᵗ parameter must be a file that exists" %+ goto :END)

rem Unset holistic flags:
        unset /q QUICK_LRC_FAILED QUICK_LRC_SKIPPED QUICK_LRC_SUCCESS

rem Pass to get-lyrics in “quick LRC” mode:
        call get-lyrics-for-file.btm "%FILE%" quick_lrc %2$



:END

