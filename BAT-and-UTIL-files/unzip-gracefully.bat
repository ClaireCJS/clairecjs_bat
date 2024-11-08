@Echo off



    
:: validation:
            set ZIP=%@UNQUOTE[%1]  
            rem call print-if-debug d* ZIP=[%ZIP%]
            rem         if not isdir "%ZIP%" (echo * FOLDER: NO.)
            rem         if     isdir "%ZIP%" (echo * FOLDER: YES.)
                        if     isdir "%ZIP%" (call error "First arg of %ZIP% can't be a directory, silly!"  %+ goto :END)

:: setup:
        set         FILENAME_OLD=%ZIP%
        set         FILENAME_NEW=%ZIP%
        set             TO_UNZIP=%@UNQUOTE[%FILENAME_NEW%]
        set             BASENAME=%@NAME[%TO_UNZIP%]
        set TO_UNZIP_EXTENSION_1=%@UPPER[%@EXT[%TO_UNZIP%]]                          %+ rem will capture 7z for "file.7z"
        set TO_UNZIP_EXTENSION_2=%@UPPER[%@EXT[%BASENAME%]]                          %+ rem will capture 7z for "file.7z.001"
        rem call debug "BASENAME             is '%BASENAME%'"
        rem call debug "TO_UNZIP_EXTENSION_1 is '%TO_UNZIP_EXTENSION_1%'"
        rem call debug "TO_UNZIP_EXTENSION_2 is '%TO_UNZIP_EXTENSION_2%'"
        if "%TO_UNZIP_EXTENSION_1%" != "7Z"  (set USE_7Z=0  %+ set NUMBERED=0)
        if "%TO_UNZIP_EXTENSION_1%" != "RAR" (set USE_RAR=0 %+ set NUMBERED=0)
        
        if "%TO_UNZIP_EXTENSION_1%" == "7Z"  (set USE_7Z=1  %+ set NUMBERED=0)
        if "%TO_UNZIP_EXTENSION_1%" == "RAR" (set USE_RAR=1 %+ set NUMBERED=0)

        if "%TO_UNZIP_EXTENSION_2%" == "7Z"  (set USE_7Z=1  %+ set NUMBERED=1)
        if "%TO_UNZIP_EXTENSION_2%" == "RAR" (set USE_RAR=1 %+ set NUMBERED=1)       %+ rem not sure if this will work


    set                                                                            WE_CAN_DEAL_WITH_THIS_EXTENSION=0
    if "%TO_UNZIP_EXTENSION_1" ==  "7Z" .or. "%TO_UNZIP_EXTENSION_2" ==  "7Z" (set WE_CAN_DEAL_WITH_THIS_EXTENSION=1)
    if "%TO_UNZIP_EXTENSION_1" == "RAR" .or. "%TO_UNZIP_EXTENSION_2" == "RAR" (set WE_CAN_DEAL_WITH_THIS_EXTENSION=1)
    if "%TO_UNZIP_EXTENSION_1" == "ZIP" .or. "%TO_UNZIP_EXTENSION_2" == "ZIP" (set WE_CAN_DEAL_WITH_THIS_EXTENSION=1)
    if %WE_CAN_DEAL_WITH_THIS_EXTENSION eq 0 (call warning "We don't know how to deal with the '%ITALICS_ON%%BLINK_ON%%TO_UNZIP_EXTENSION_1%%ITALICS_OFF%%BLINK_OFF%' extension and will be skipping it!" %+ pause %+ goto :Skip_To_Here_If_Extension_Is_Unknown)

:: do it:
        *md "%BASENAME%"
        *cd "%BASENAME%"
        rem moving the zip into the folder also solves the problem of losing track of which zips are unzipped when interrupted [the ones not done are not moved into their folder, though the last interrupted one is which requires paying attention]
        rem echo if %NUMBERED ne 1 (move /q ..\"%TO_UNZIP%"            )
        echos %ANSI_COLOR_REMOVAL%%FAINT_ON%%ITALICS_ON%
                 if %NUMBERED ne 1 (move /Ns /g ..\"%TO_UNZIP%"            )
                 if %NUMBERED eq 1 (move /Ns /g ..\"%BASENAME%.0[0-9][0-9]")
                         rem pause
        echos %FAINT_OFF%%ITALICS_OFF%%ANSI_RESET%
        rem echo on
        rem %color_debug% %+ dir
        echo.
        %COLOR_RUN%
        set DISPLAY_NAME='%emphasis%%TO_UNZIP%%deemphasis%'
        rem call debug "USE_7Z == %USE_7Z , USE_RAR == %USE_RAR , TO_UNZIP= %TO_UNZIP%"
        rem if %USE_7Z eq 1 .and. %USE_RAR ne 1 (echo %STAR%%@RANDFG[]7unzipping %DISPLAY_NAME%...%@RANDFG[] %+  *7unzip /E /O /P    "%TO_UNZIP%"|& copy-move-post.py ) 
            if %USE_7Z ne 1 .and. %USE_RAR ne 1 (echo %STAR%%@RANDFG[ ]Unzipping %DISPLAY_NAME%...%@RANDFG[] %+    unzip /E /O /D /I "%TO_UNZIP%"|&:u8 copy-move-post.py )
            if %USE_7Z eq 1 .and. %USE_RAR ne 1 (echo %STAR%%@RANDFG[]7unzipping %DISPLAY_NAME%...%@RANDFG[] %+   7z.exe x -aoa      "%TO_UNZIP%"|&:u8 copy-move-post.py ) 
            if %USE_7Z ne 1 .and. %USE_RAR eq 1 (echo %STAR%%@RANDFG[  ]UnRARing %DISPLAY_NAME%...%@RANDFG[] %+ call rar x  -o+      "%TO_UNZIP%"|&:u8 copy-move-post.py )
        call errorlevel "problem uncompressing %DISPLAY_NAME%"
        REM -ao - set overwrite mode
        echo.
        echo %ANSI_RESET%%@ANSI_MOVE_TO_COL[1]%CHECK% %ANSI_COLOR_SUCCESS%Uncompressed %DISPLAY_NAME%%ANSI_COLOR_SUCCESS%%ANSI_RESET%%ANSI_EOL%
        echos %ANSI_COLOR_SUCCESS%%FAINT_ON%
        dir   
        echos %FAINT_OFF%%ANSI_RESET%
        set FILECOUNT=%@FILES[/s/h,*]
        echo.
        rem echo call AskYN "Delete the original archive" no 15
                set  AskYN_question=Delete the original archive
                call AskYN overriddenbyenvvar no 8
                                                 set WE_DELETE=0
                           if "%ANSWER%" == "Y" (set WE_DELETE=1)
        rem call debug "file count == %FILECOUNT%, WE_DELETE == %WE_DELETE%, NUMBERED == %NUMBERED%, TO_UNZIP == '%TO_UNZIP%', CWP == %_CWP"
        if %WE_DELETE eq 1 .and. %@FILES[/s/h,*] gt 1                      (del /p "%TO_UNZIP%"            )  %+ rem 20151105 added filecheck to make sure something actually unzipped
        if %WE_DELETE eq 1 .and. %@FILES[/s/h,*] gt 1 .and. %NUMBERED eq 1 (del /p "%BASENAME%.0[0-9][0-9]")  %+ rem 20151105 added filecheck to make sure something actually unzipped
        rem call print=if-debug "folder is '%_CWP'"
        if %@FILES[/s/h,*] lt 1 (goto :Error)
        :ErrorDone
        cd ..

rem         if isdir "%BASENAME%\%@NAME["%FILENAME_OLD%"]" (%COLOR_REMOVAL% %+ mv/ds  "%BASENAME%\%@NAME["%FILENAME_OLD%"]" "%BASENAME%" %+ %COLOR_NORMAL%)
        rem ^^^^^^^^^^^^^^^ This last line address the situation of zip files that have a folder with the ZIP's own name in them 
        rem 2024——not sure if we still need to do this, taking it out for a bit

:: cleanup:
    :Skip_To_Here_If_Extension_Is_Unknown

goto :END

    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :Error
            call error "Uh oh from %0"
        goto :ErrorDone
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:END
