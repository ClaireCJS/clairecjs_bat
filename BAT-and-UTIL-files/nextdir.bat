@Echo off

:DESCRIPTION: this simply goes to the next folder, alphabetically. A lateral folder move. 
:DESCRIPTION: But it also has some folder-specific auto-reaction stuff

::::: ENVIRONMENT VALIDATION:
    call checktemp


::::: Take a file along with us, if one is given: part 1 of 2:
    if exist %1 set FILE_TO_MOVE=%@UNQUOTE[%@TRUENAME[%1]]

::::: Take some files along with us automatically:
    set AUTOMOVE_FILE_1=___ Claire's caption writing up to here ____
    set AUTOMOVE_FILE_2=___ caption writing up to here ____
    set AUTOMOVE_FILE_3=___ precursory review up to here ____
    set AUTOMOVE_FILE_4=__ precursory review up to here __
    set AUTOMOVE_FILE_5=__ Carolyn tagging up to here __
    if exist "%AUTOMOVE_FILE_1%" (set FILE_TO_MOVE_1=%@UNQUOTE[%@TRUENAME[%AUTOMOVE_FILE_1%]])
    if exist "%AUTOMOVE_FILE_2%" (set FILE_TO_MOVE_2=%@UNQUOTE[%@TRUENAME[%AUTOMOVE_FILE_2%]])
    if exist "%AUTOMOVE_FILE_3%" (set FILE_TO_MOVE_3=%@UNQUOTE[%@TRUENAME[%AUTOMOVE_FILE_3%]])
    if exist "%AUTOMOVE_FILE_4%" (set FILE_TO_MOVE_4=%@UNQUOTE[%@TRUENAME[%AUTOMOVE_FILE_4%]])
    if exist "%AUTOMOVE_FILE_5%" (set FILE_TO_MOVE_5=%@UNQUOTE[%@TRUENAME[%AUTOMOVE_FILE_5%]])
    if exist "%AUTOMOVE_FILE_6%" (set FILE_TO_MOVE_6=%@UNQUOTE[%@TRUENAME[%AUTOMOVE_FILE_6%]])
    if exist "%AUTOMOVE_FILE_7%" (set FILE_TO_MOVE_7=%@UNQUOTE[%@TRUENAME[%AUTOMOVE_FILE_7%]])
    if exist "%AUTOMOVE_FILE_8%" (set FILE_TO_MOVE_8=%@UNQUOTE[%@TRUENAME[%AUTOMOVE_FILE_8%]])
    if exist "%AUTOMOVE_FILE_9%" (set FILE_TO_MOVE_9=%@UNQUOTE[%@TRUENAME[%AUTOMOVE_FILE_9%]])


::::: MOVE TO THE NEXT FOLDER:
    set TARGET_TEMP_SCRIPT="%TEMP\go-to-next-directory.bat"
    go-to-next-directory-generator.pl "%_CWD" >:u8 %TARGET_TEMP_SCRIPT%
    REM echo done with perl
    call %TARGET_TEMP_SCRIPT%

::::: Take a file along with us, if one is given: part 2 of 2:
    if "%FILE_TO_MOVE%" eq "" goto :NoFileToMove
        mv "%FILE_TO_MOVE%" .
        set FILE_THAT_WAS_MOVED=%FILE_TO_MOVE%
        unset /Q FILE_TO_MOVE
    :NoFileToMove

::::: Take a file along with us, automatically:
    if "%ACTIVITY%" eq "TAGGING" .or. "%@REGEX[NEW.*PICT*U*R*E*S,%@UPPER[%_CWD]]" eq "1" goto :Move_YES
    goto :Move_NO
        :Move_YES
            :DEBUG STUFF: echo move yes %+ pause %+ echo on
            if defined FILE_TO_MOVE_1 (mv "%FILE_TO_MOVE_1%" . %+ set FILE_THAT_WAS_MOVED_1=%FILE_TO_MOVE_1% %+ unset /Q FILE_TO_MOVE_1)
            if defined FILE_TO_MOVE_2 (mv "%FILE_TO_MOVE_2%" . %+ set FILE_THAT_WAS_MOVED_1=%FILE_TO_MOVE_2% %+ unset /Q FILE_TO_MOVE_2)
            if defined FILE_TO_MOVE_3 (mv "%FILE_TO_MOVE_3%" . %+ set FILE_THAT_WAS_MOVED_1=%FILE_TO_MOVE_3% %+ unset /Q FILE_TO_MOVE_3)
            if defined FILE_TO_MOVE_4 (mv "%FILE_TO_MOVE_4%" . %+ set FILE_THAT_WAS_MOVED_1=%FILE_TO_MOVE_4% %+ unset /Q FILE_TO_MOVE_4)
            if defined FILE_TO_MOVE_5 (mv "%FILE_TO_MOVE_5%" . %+ set FILE_THAT_WAS_MOVED_1=%FILE_TO_MOVE_5% %+ unset /Q FILE_TO_MOVE_5)
            if defined FILE_TO_MOVE_6 (mv "%FILE_TO_MOVE_6%" . %+ set FILE_THAT_WAS_MOVED_1=%FILE_TO_MOVE_6% %+ unset /Q FILE_TO_MOVE_6)
            if defined FILE_TO_MOVE_7 (mv "%FILE_TO_MOVE_7%" . %+ set FILE_THAT_WAS_MOVED_1=%FILE_TO_MOVE_7% %+ unset /Q FILE_TO_MOVE_7)
            if defined FILE_TO_MOVE_8 (mv "%FILE_TO_MOVE_8%" . %+ set FILE_THAT_WAS_MOVED_1=%FILE_TO_MOVE_8% %+ unset /Q FILE_TO_MOVE_8)
            if defined FILE_TO_MOVE_9 (mv "%FILE_TO_MOVE_9%" . %+ set FILE_THAT_WAS_MOVED_1=%FILE_TO_MOVE_9% %+ unset /Q FILE_TO_MOVE_9)
        :Move_NO


::::: Show that we're done:
    dir

