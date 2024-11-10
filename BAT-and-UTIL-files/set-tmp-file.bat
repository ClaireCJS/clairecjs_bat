@Echo OFF


rem Validate environment:
        if 1 ne %SETTMPFILE_VALIDATED (
            call validate-environment-variables TEMP KNOWN_NAME
            set SETTMPFILE_VALIDATED=1
        )



rem Generate components of our temp filename:
        SET TMPFILE_DIR=%TEMP%
        SET TMPFILE_FILE=%_DATETIME.%KNOWN_NAME%.%_PID.%@NAME[%@UNIQUE[%TEMP]]

        rem Aliases for easier auditing:
                SET TMPFILE_FILENAME=%TMPFILE_FILE%
                SET TMPFILENAME=%TMPFILE_FILE%
                SET TMP_FILENAME=%TMPFILE_FILE%
                SET TMP_FILE_NAME=%TMPFILE_FILE%

                SET TMPFILE_PRE=%TMPFILE_DIR%
                SET TMPFILE_POST=%TMPFILE_FILE%

                SET TMPFILE_LEFT=%TMPFILE_DIR%
                SET TMPFILE_RIGHT=%TMPFILE_FILE%



rem Set the actual, full tmpfile name:
    SET TMPFILE=%TMPFILE_DIR%\%TMPFILE_FILE%               
    
rem BE VERY CAREFUL WITH DEBUG OUTPUT!! It can mess up stuff when this is buried deep within cosmetic/ansi-complicated stuff
    if 1 eq %DEBUG_TMPFILE (call debug "TMPFILE is '%TMPFILE%'")



