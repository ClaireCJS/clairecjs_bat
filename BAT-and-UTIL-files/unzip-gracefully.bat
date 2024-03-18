@Echo off

:: manual configuratio:
    ::::set to "::::"  under normal conditions, "echo" for debug conditions:
    set      DEBUG_THING_1=::::                                           
    unset /q DEBUG_THING_2

:: environment configuration:
    if "%DEBUG%" eq "1" (set DEBUG_THING_1=echo %+ set DEBUG_THING_2=echo)

    
:: validation:
    set ZIP=%@UNQUOTE[%1]  %+     call print-if-debug d* ZIP=[%ZIP%]
:   %DEBUG_THING_1% if not isdir "%ZIP%" (echo * FOLDER: NO.)
:                   if not isdir "%ZIP%" (echo * FOLDER: NO.)
:   %DEBUG_THING_1% if     isdir "%ZIP%" (echo * FOLDER: YES.)
:                   if     isdir "%ZIP%" (echo * FOLDER: YES.)
:   %DEBUG_THING_1% if     isdir "%ZIP%" (echo * ERROR: First arg of %ZIP% can't be a directory, silly! %+ beep %+ pause %+ goto :END)
                    if     isdir "%ZIP%" (echo * ERROR: First arg of %ZIP% can't be a directory, silly! %+ beep %+ pause %+ goto :END)

:: setup:
    set FILENAME_OLD=%ZIP%
    set FILENAME_NEW=%ZIP%
    set TO_UNZIP=%@UNQUOTE[%FILENAME_NEW%]
    set BASENAME=%@NAME[%TO_UNZIP%]
    set TO_UNZIP_EXTENSION_1=%@UPPER[%@EXT[%TO_UNZIP%]]                          %+ rem will capture 7z for "file.7z"
    set TO_UNZIP_EXTENSION_2=%@UPPER[%@EXT[%BASENAME%]]                          %+ rem will capture 7z for "file.7z.001"
    rem call debug "BASENAME             is '%BASENAME%'"
    rem call debug "TO_UNZIP_EXTENSION_1 is '%TO_UNZIP_EXTENSION_1%'"
    rem call debug "TO_UNZIP_EXTENSION_2 is '%TO_UNZIP_EXTENSION_2%'"
    if "%TO_UNZIP_EXTENSION_2%"    ne "7Z" (set USE_7Z=0 %+ set NUMBERED=0)
    if "%TO_UNZIP_EXTENSION_1%"    ne "7Z" (set USE_7Z=0 %+ set NUMBERED=0)
    if "%TO_UNZIP_EXTENSION_1%"    eq "7Z" (set USE_7Z=1 %+ set NUMBERED=0)
    if "%TO_UNZIP_EXTENSION_2%"    eq "7Z" (set USE_7Z=1 %+ set NUMBERED=1)
    if %USE_7Z ne 1 (set EXTRACTOR=unzip /E /D /I /O)
    if %USE_7Z eq 1 (set EXTRACTOR=7z x -aoa        )                            %+ REM -ao - set overwrite mode

    set                                                                            WE_CAN_DEAL_WITH_THIS_EXTENSION=0
    if "%TO_UNZIP_EXTENSION_1" eq  "7Z" .or. "%TO_UNZIP_EXTENSION_2" eq  "7Z" (set WE_CAN_DEAL_WITH_THIS_EXTENSION=1)
    if "%TO_UNZIP_EXTENSION_1" eq "RAR" .or. "%TO_UNZIP_EXTENSION_2" eq "RAR" (set WE_CAN_DEAL_WITH_THIS_EXTENSION=1)
    if "%TO_UNZIP_EXTENSION_1" eq "ZIP" .or. "%TO_UNZIP_EXTENSION_2" eq "ZIP" (set WE_CAN_DEAL_WITH_THIS_EXTENSION=1)
    if %WE_CAN_DEAL_WITH_THIS_EXTENSION eq 0 (call warning "We don't know how to deal with the '%ITALICS_ON%%BLINK_ON%%TO_UNZIP_EXTENSION_1%%ITALICS_OFF%%BLINK_OFF%' extension and will be skipping it!" %+ pause %+ goto :Skip_To_Here_If_Extension_Is_Unknown)

:: do it:
        %DEBUG_THING_2%  md "%BASENAME%"
        %DEBUG_THING_2%  cd "%BASENAME%"
        %DEBUG_THING_2%  move ..\"%TO_UNZIP%"
        %DEBUG_THING_2%  if %NUMBERED eq 1 (move ..\"%BASENAME%.0[0-9][0-9]")
                         %COLOR_RUN%
        %DEBUG_THING_2%  %EXTRACTOR% "%TO_UNZIP%"
        %DEBUG_THING_2%  if %@FILES[/s/h,*] gt 1 (del "%TO_UNZIP%")  %+ REM 20151105 added filecheck to make sure somethign actually unzipped
        %DEBUG_THING_2%  if %@FILES[/s/h,*] gt 1 .and. %NUMBERED eq 1 (del "%BASENAME%.0[0-9][0-9]")  %+ REM 20151105 added filecheck to make sure somethign actually unzipped
        :DEBUG: echo folder is %_CWP    pause
        %DEBUG_THING_2%  if %@FILES[/s/h,*] lt 1 (goto :Error)
        :ErrorDone
        %DEBUG_THING_2%  cd ..
        %DEBUG_THING_2%  dir "%BASENAME%"
        %DEBUG_THING_2%  if isdir "%BASENAME%\%@NAME["%FILENAME_OLD%"]" mv/ds  "%BASENAME%\%@NAME["%FILENAME_OLD%"]" "%BASENAME%"
        :: ^^ That last line address the situation of zip files that have a folder with the ZIP's own name in them by collapsing the original name into the new name, to create a subfolder with the same name as an enclosing folder, which is stupid

:: cleanup:
    :Skip_To_Here_If_Extension_Is_Unknown
    unset /q DEBUG_THING_1
    unset /q DEBUG_THING_2

goto :END

    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :Error
            call error "Uh oh from %0..."
        goto :ErrorDone
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:END
