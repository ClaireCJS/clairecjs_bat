@Echo off
 on break cancel
 echo.

rem CONFIG:
        set TIME_TO_WAIT_BEFORE_DELETING_ORIGINAL_FILE=30


rem Parameter checking:
        set FILE_TO_ZIP=%@UNQUOTE[%1]
        call validate-environment-variable FILE_TO_ZIP "zip-file called on file that doesn’t exist: %italics%“%FILE_TO_ZIP%”"


rem Create new zip file name & set up ZIP command:
        set TARGET_ZIP=%@UNQUOTE[%@NAME[%FILE_TO_ZIP]].zip
        set ZIP_COMMAND=*zip /A /F "%TARGET_ZIP%" "%FILE_TO_ZIP%"
        if %DEBUG eq 1 (echo %ANSI_COLOR_DEBUG%- ZIP_COMMAND is: %ITALICS_ON%%ZIP_COMMAND%%ITALICS_OFF%)             %+ rem Don’t use debug.bat/print-message debug because it destroys the quotes we really want to see


rem Do the actual ZIP’ing...
        rem old: call zip-old %FILER
        rem new:
        echo %ANSI_COLOR_DEBUG%%BOLD_ON%%WRENCH% ZIP’ing “%italics_on%%double_underline_on%%@UNQUOTE[%FILE_TO_ZIP%]%double_underline_off%%italics_off%” into “%italics_on%%double_underline_on%%TARGET_ZIP%%double_underline_off%%italics_off%”...%BOLD_OFF%%ANSI_COLOR_RUN%
        %COLOR_RUN%
        %ZIP_COMMAND%  |:u8 call insert-before-each-line "        "

        rem Make sure it went well...
            call errorlevel "error when zipping file %file_to_zip% in %0"
            if %@FILESIZE["%TARGET_ZIP"] lt 1 (call fatal_error "created zip of “%TARGET_ZIP%” has no valid file size!" %+ goto :END)

rem LEt user know it was successfully ZIP’ed so they can feel confident deleting the original file:
        iff exist "%TARGET_ZIP%" then
                %COLOR_SUCCESS% %+ echo. %+ echo %ANSI_COLOR_SUCCESS%%BOLD_ON%%CHECKBOX% ZIP created:%BOLD_OFF%%ANSI_COLOR_RUN%
                dir "%TARGET_ZIP%" /km |:u8 call insert-before-each-line "        "
        else
                call alarm "Target ZIPfile does not exist: “%italics_on%%TARGET_ZIP%%italics_on%”"
                goto :Zip_Was_Not_Created
        endiff


rem Delete the original file?
        echo.
        call askyn "%GHOST% Delete “%italics_on%%double_underline_on%%FILE_TO_ZIP%”%italics_off%%double_underline_off%" yes %TIME_TO_WAIT_BEFORE_DELETING_ORIGINAL_FILE%
        if %DO_IT eq 1 (
            %COLOR_REMOVAL%
            echos %FAINT_ON%                                                                 |:u8 fast_cat
            *del "%FILE_TO_ZIP%" |:u8 call insert-before-each-line "        %ANSI_FAINT_ON%" |:u8 fast_cat
            echos %FAINT_OFF%                                                                |:u8 fast_cat
            rem (fast_cat fixes TCC ansi display errors)
        )


rem Success output:
        %COLOR_SUCCESS% %+ echo. %+ echo %ANSI_COLOR_SUCCESS%%BOLD_ON%%CHECKBOX% ZIP created:%BOLD_OFF%%ANSI_COLOR_RUN%
        dir "%TARGET_ZIP%" /km |:u8 call insert-before-each-line "        "
        %COLOR_SUCCESS% %+ echo. %+ echo %ANSI_COLOR_DEBUG%%BOLD_ON%%CHECKBOX% Contents of ZIP “%italics_on%%double_underline_on%%TARGET_ZIP%%double_underline_off%%italics_off%”:%BOLD_OFF%%ANSI_COLOR_RUN%
        *zip /v "%TARGET_ZIP%" |:u8 call insert-before-each-line "        "



:Zip_Was_Not_Created
:END

