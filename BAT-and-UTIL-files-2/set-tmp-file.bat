@Echo OFF
@on break cancel


rem usage:
        iff "%1" == "?" .or. "%1" == "/?" .or. "%1" == "-?" .or. "%1" == "/h" .or. "%1" == "/help" .or. "%1" == "-h" .or. "%1" == "--help" then
                echo :USAGE: call set-tmp-file
                echo :USAGE: call set-tmp-file [nature of temp file]
                echo :USAGE: call set-tmp-file "AI encoding"
                echo :USAGE:
                echo :USAGE: sets %%tmpfile / %%tempfile / %%tmp_file
                echo :USAGE: sets %%tmpfile_filename / %%temp_file_name
                echo :USAGE: sets %%temp_file_dir
        endiff


rem Validate environment:
        iff "1" != "%SETTMPFILE_VALIDATED" then
                if not defined TEMP       call validate-environment-variable TEMP 
                if not defined KNOWN_NAME call validate-environment-variable KNOWN_NAME "Known_name should be set to your username"
                set  SETTMPFILE_VALIDATED=1
        endiff

rem Grab parameters:
        iff "%1" != "" then
                set nature=%@UNQUOTE[%@Replace[ ,_,"%1"]].
                shift
        else
                set nature=
        endiff


rem Generate components of our temp filename:

        SET TMP_FILE_FILE=%_DATETIME.%KNOWN_NAME%.%[NATURE]%_PID.%@NAME[%@UNIQUEx[%TEMP%\]]
        SET TMP_FILE_FILE1=%TMP_FILE_FILE%
        SET TMP_FILE_FILE2=%_DATETIME.%KNOWN_NAME%.%[NATURE]%_PID.%@NAME[%@UNIQUEx[%TEMP%\]]
        SET TMP_FILE_FILE3=%_DATETIME.%KNOWN_NAME%.%[NATURE]%_PID.%@NAME[%@UNIQUEx[%TEMP%\]]
        SET TMP_FILE_FILE4=%_DATETIME.%KNOWN_NAME%.%[NATURE]%_PID.%@NAME[%@UNIQUEx[%TEMP%\]]
        SET TMP_FILE_FILE5=%_DATETIME.%KNOWN_NAME%.%[NATURE]%_PID.%@NAME[%@UNIQUEx[%TEMP%\]]
                SET TEMP_FILE_FILE=%TMP_FILE_FILE%
                SET TMPFILE_FILE=%TMP_FILE_FILE%
                SET TEMPFILE_FILE=%TMP_FILE_FILE%
                SET TMPFILE_FILENAME=%TMPFILE_FILE%
                SET TEMPFILE_FILENAME=%TMPFILE_FILE%
                SET TMP_FILE_FILENAME=%TMPFILE_FILE%
                SET TEMP_FILE_FILENAME=%TMPFILE_FILE%
                SET TMPFILE_NAME=%TMPFILE_FILE%
                SET TEMPFILE_NAME=%TMPFILE_FILE%
                SET TMPFILENAME=%TMPFILE_FILE%
                SET TEMPFILENAME=%TMPFILE_FILE%
                SET TMP_FILE_NAME=%TMPFILE_FILE%
                SET TEMP_FILE_NAME=%TMPFILE_FILE%
                SET TMP_FILENAME=%TMPFILE_FILE%
                SET TEMP_FILENAME=%TMPFILE_FILE%
                SET TMPFILE_POST=%TMPFILE_FILE%
                SET TEMPFILE_POST=%TMPFILE_FILE%
                SET TMP_FILE_POST=%TMPFILE_FILE%
                SET TEMP_FILE_POST=%TMPFILE_FILE%
                SET TMPFILE_RIGHT=%TMPFILE_FILE%
                SET TEMPFILE_RIGHT=%TMPFILE_FILE%
                SET TMP_FILE_RIGHT=%TMPFILE_FILE%
                SET TEMP_FILE_RIGHT=%TMPFILE_FILE%

        SET TMPFILE_DIR=%TEMP%
                SET TEMPFILE_DIR=%TMPFILE_DIR%
                SET TMP_FILE_DIR=%TMPFILE_DIR%
                SET TEMP_FILE_DIR=%TMPFILE_DIR%
                SET TMP_FILE_FOLDER=%TMP_FILE_DIR%
                SET TEMP_FILE_FOLDER=%TMP_FILE_DIR%
                SET TMPFILE_FOLDER=%TMP_FILE_DIR%
                SET TEMPFILE_FOLDER=%TMP_FILE_DIR%
                SET TMPFILE_PRE=%TMPFILE_DIR%
                SET TEMPFILE_PRE=%TMPFILE_DIR%
                SET TMP_FILE_PRE=%TMPFILE_DIR%
                SET TEMP_FILE_PRE=%TMPFILE_DIR%
                SET TMPFILE_LEFT=%TMPFILE_DIR%
                SET TEMPFILE_LEFT=%TMPFILE_DIR%
                SET TMP_FILE_LEFT=%TMPFILE_DIR%
                SET TEMP_FILE_LEFT=%TMPFILE_DIR%

       
rem Set the actual, full tmpfile name:
     SET TMP_FILE_FULL=%TMPFILE_DIR%\%TMP_FILE_FILE1%               
    SET TMP_FILE_FULL2=%TMPFILE_DIR%\%TMP_FILE_FILE2%               
    SET TMP_FILE_FULL3=%TMPFILE_DIR%\%TMP_FILE_FILE3%               
    SET TMP_FILE_FULL4=%TMPFILE_DIR%\%TMP_FILE_FILE4%               
    SET TMP_FILE_FULL5=%TMPFILE_DIR%\%TMP_FILE_FILE5%               
            SET TMPFILE_FULL=%TMP_FILE_FULL%
            SET    TEMP_FILE=%TMP_FILE_FULL%
            SET     TEMPFILE=%TMP_FILE_FULL%
            SET     TMP_FILE=%TMP_FILE_FULL%
            SET      TMPFILE=%TMP_FILE_FULL%
            SET     TMPFILE1=%TMP_FILE_FULL%
            SET     TMPFILE2=%TMP_FILE_FULL2%
            SET     TMPFILE3=%TMP_FILE_FULL3%
            SET     TMPFILE4=%TMP_FILE_FULL4%
            SET     TMPFILE5=%TMP_FILE_FULL5%
    
rem BE VERY CAREFUL WITH DEBUG OUTPUT!! It can mess up stuff when this is buried deep within cosmetic/ansi-complicated stuff
    if 1 eq %DEBUG_TMPFILE (call debug "TMPFILE is '%TMPFILE%'")



