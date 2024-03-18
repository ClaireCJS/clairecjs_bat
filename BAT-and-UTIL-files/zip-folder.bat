@echo on

set WHAT_FOLDER_TO_ZIP=%1
rem ZIP_OPTIONS=%2 %3 %4 %5 %6 %7 %8 %9
set ZIP_OPTIONS=%2$


call print-if-debug "*** CALLED: zip.bat %* from CWD=%_CWD and WHAT_FOLDER_TO_ZIP is '%WHAT_FOLDER_TO_ZIP%'"
if "%DEBUG%" eq "1" (dir %+ pause)



:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::: Is this a folder, or a file?
     if "*" eq "%WHAT_FOLDER_TO_ZIP%" goto :itsafile
     if isdir   %WHAT_FOLDER_TO_ZIP%  goto :itsadir
     if exist   %WHAT_FOLDER_TO_ZIP%  goto :itsafile
     call error "WHAT_FOLDER_TO_ZIP of %WHAT_FOLDER_TO_ZIP% is neither a file nor a folder?!"
     call white-noise 1
     pause
     goto :end
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::






:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::: If it's a folder, we need to come up with a ZIP name:
:itsadir
    set     DIR="%@STRIP[%=",%WHAT_FOLDER_TO_ZIP%]"
    set ARCHIVE="%@STRIP[%="\,%WHAT_FOLDER_TO_ZIP%].zip"
    if "%DEBUG%" eq "1" (call print-if-debug * DIR is %DIR , archive name will be %ARCHIVE %+ pause)

    %COLOR_GREP% %+  echos * ZIP: %WHAT_FOLDER_TO_ZIP% %+ %COLOR_NORMAL% %+ echo.


    ::::: Windows 7 implies we are using TCC instead of 4NT, which has a zip command internally
    ::::: Otherwize, we use the wzzip command-line extension to WinZip (downloadable from winzip.com)
    %COLOR_RUN%
    if "%OS"=="10" .or. "%OS%" eq "11" goto :Internal_TCC_ZIP
    if "%OS"=="7" goto :Win7
                                call debug "Still using windows 7...
                                call wzzip -r -p %ZIP_OPTIONS% %ARCHIVE% %DIR\*.*
                  goto :NotWin7

        :Win7
             %COLOR_IMPORTANT% %+ echo *zip /r /p %ARCHIVE% %DIR\*.*
             %COLOR_RUN%       %+      *zip /r /p %ARCHIVE% %DIR\*.*
        goto :DoneZippingDir

        :NotWin7
            unzip -v %ZIP_OPTIONS% %ARCHIVE%
        :DoneZippingDir


        :Win10
        :Win11
            goto :Internal_TCC_ZIP

        :Internal_TCC_ZIP
            *zip /A /F /P /R /Z"BAT files associated with this project"  %ZIP_OPTIONS% %ARCHIVE% %DIR\*.*

    ::::: Now get rid of the folder, because we zipped it:
        ::or did we?
        if     exist %ARCHIVE% (goto :Archive_Exists_After_Done_YES)
        if not exist %ARCHIVE% (goto :Archive_Exists_After_Done_NO )
                :Archive_Exists_After_Done_YES
                                            call success "Archive has been created."
                    :COLOR_RUN%       %+    echo * AUTO_DEL_DIR=%AUTO_DEL_DIR%       %+ %COLOR_REMOVAL%
                    if %AUTO_DEL_DIR% eq 1 (echo r | deltree %DIR%)
                    if %AUTO_DEL_DIR% ne 1 (         deltree %DIR%)
                    %COLOR_SUCCESS    %+    call removal "Original folder has been deleted"
                goto :Archive_Step_DONE
                :Archive_Exists_After_Done_NO
                    call ERROR "Archive does not exist: '%ARCHIVE%'"
                    pause
                goto :Archive_Step_DONE
        :Archive_Step_DONE

    ::::: Move the data to %DATA, where it will eventually be burned:
        if "%_CWP"=="\new" if exist %ARCHIVE% call data /p %ARCHIVE%
goto :end
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::





:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:itsafile_OLD
    call error "zip-folder called on file '%WHAT_FOLDER_TO_ZIP%'"
    goto :END
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:itsafile_OLD
    ::::: figure out the zip name:
    set ARCHIVE="%@STRIP[%=",%@NAME[%WHAT_FOLDER_TO_ZIP%]].zip"
    :DEBUG: echo BASE IS %BASE%, ARCHIVE IS %ARCHIVE%

    %COLOR_RUN%
    if "%OS"=="7" goto :Win7
            echo * call wzzip %ZIP_OPTIONS% %ARCHIVE% %WHAT_FOLDER_TO_ZIP%
                   call wzzip %ZIP_OPTIONS% %ARCHIVE% %WHAT_FOLDER_TO_ZIP%
        goto :NotWin7

        :Win7
            echo *zip %ZIP_OPTIONS% %ARCHIVE% %WHAT_FOLDER_TO_ZIP%
                 *zip %ZIP_OPTIONS% %ARCHIVE% %WHAT_FOLDER_TO_ZIP%
        :NotWin7

    ::::: show the directory:
    echo. %+ echo. %+ echo. %+ dir /km %ARCHIVE% %+ echo. %+ echo. %+ echo. %+ echo. 

    ::::: Delete the file (maybe):
    if %AUTO_DEL%      eq 1 (goto :AutoDel_YES)
    if %AUTO_DEL_FILE% eq 1 (goto :AutoDel_YES)
    if %AUTO_DEL_DIR%  eq 1 (goto :AutoDel_YES)
            :AutoDel_YES
                          %COLOR_REMOVAL%
                echo ry | del /p %WHAT_FOLDER_TO_ZIP%
            goto :AutoDel_END
            :AutoDel_NO
                          %COLOR_REMOVAL%
                          del /p %WHAT_FOLDER_TO_ZIP%
            goto :AutoDel_END
        :AutoDel_END
        %COLOR_NORMAL%

    ::::: Move the data to %DATA, where it will eventually be burned:
    if "%_CWP"=="\new" if exist %ARCHIVE% call data /p %ARCHIVE%
goto :end
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::





:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:itsnothing
    %COLOR_ERROR%
    call error "Sorry, %WHAT_FOLDER_TO_ZIP% doesn't exist!"
    pause
goto :end
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::






:end

call important_less "TIP: set AUTO_DEL_DIR=1 to automatically deltree the dir after success."
call warning "Be careful!!!!!"

call success "DONE!"

echo. %+ echo. %+ echo. %+ echo.


