@Echo OFF

::::: IF WE PASS A SINGLE-DIGIT NUMBER, WE ARE PROBABLY TRYING TO CALL DP.BAT INSTEAD OF PD.BAT, SO LET'S JUST ALLOW THAT:
    SET ARGV=%1
    if "%ARGV%" eq "" goto :NoOverload
        :Overload
        if "%ARGV%" ne "" .and. "%@LEN[%ARGV%]" eq "1" .and. "%2" eq "" .and. "%@REGEX[[0-%_MONITORS],%ARGV%]" eq "1" (dp.bat %*)
    :NoOverload

::::: Take a file along with us, if one is given: part 1 of 2:
    if exist %1 set FILE_TO_MOVE=%@UNQUOTE[%@TRUENAME[%1]]

::::: ACTUAL PD.BAT (which could be refactored into a parameterized call to ND.bat, really):
    call checktemp
    set TARGET="%TEMP\go-to-next-directory.bat"
    go-to-next-directory-generator.pl "%_CWD" PREVIOUS >%TARGET
    call %TARGET

::::: Take a file along with us, if one is given: part 2 of 2:
    if "%FILE_TO_MOVE%" eq "" goto :NoFileToMove
        mv "%FILE_TO_MOVE%" .
        set FILE_THAT_WAS_MOVED=%FILE_TO_MOVE%
        unset /Q FILE_TO_MOVE
    :NoFileToMove

::::: Show that we're done:
    dir

