@Echo on

:: manual configuration:
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
    %DEBUG_THING_1% if     isdir "%ZIP%" (echo * ERROR: First arg of %ZIP% can't be a directory, silly! ;  beep ;  pause ;  END)
                    if     isdir "%ZIP%" (echo * ERROR: First arg of %ZIP% can't be a directory, silly! %+ beep %+ pause %+ END)

:: setup:
    set FILENAME_OLD=%ZIP%
    set FILENAME_NEW=%ZIP%
    set TO_UNZIP=%@UNQUOTE[%FILENAME_NEW%]
    set BASENAME=%@NAME[%TO_UNZIP%]

:: do it:
        %DEBUG_THING_2%  md "%BASENAME%"
        %DEBUG_THING_2%  cd "%BASENAME%"
        %DEBUG_THING_2%  move ..\"%TO_UNZIP%"
        %DEBUG_THING_2%  unzip /E /D /I /O "%TO_UNZIP%"
        %DEBUG_THING_2%  if %@FILES[/s/h,*] gt 1 (del "%TO_UNZIP%")  %+ REM 20151105 added filecheck to make sure somethign actually unzipped
        :DEBUG: echo folder is %_CWP    pause
        %DEBUG_THING_2%  if %@FILES[/s/h,*] lt 1 (goto :Error)
        :ErrorDone`
        %DEBUG_THING_2%  cd ..
        %DEBUG_THING_2%  dir "%BASENAME%"
        %DEBUG_THING_2%  if isdir "%BASENAME%\%@NAME["%FILENAME_OLD%"]" mv/ds  "%BASENAME%\%@NAME["%FILENAME_OLD%"]" "%BASENAME%"
        :: ^^ That last line address the situation of zip files that have a folder with the ZIP's own name in them by collapsing the original name into the new name, to create a subfolder with the same name as an enclosing folder, which is stupid

:: cleanup:
    unset /q DEBUG_THING_1
    unset /q DEBUG_THING_2

goto :END

    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :Error
            %COLOR_ALARM% %+ echo Uh oh... %+ %COLOR_NORMAL% %+ call white-noise 1 %+ pause)
        goto :ErrorDone
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:END
