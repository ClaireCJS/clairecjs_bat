@Echo Off
@on break cancel

call validate-environment-variable FILEMASK_ARCHIVE
set FILEMASK_ARCHIVE_VALIDATED=1

for /a:d /h %1 in (*.*) do gosub process_folder_1 "%1"

goto :END


    :process_folder_1 [tmp_folder]
        rem Skip certain exceptions...
                if %tmp_folder% eq "!!! THIS IS ROOKIE PCVR, NOT ROOKIE SIDELOADER !!!" (return)
                if %tmp_folder% eq "DONE"                                               (return)
                echo %STAR% Processing folder %tmp_folder%...

        rem Change into folder....
                pushd .
                cd %tmp_folder%
                rem dir

        rem Decompress any archives...
                if not exist %FILEMASK_ARCHIVE% (goto :No_Zip          )
                    if exist >"__ unzipped __"  (goto :Already_Unzipped)
                    call unzip-all
                    >"__ unzipped __
                :Already_Unzipped
                :No_Zip

        rem if there are 0 files and 1 folder, collapse it
                set NUM_FILES=%@FILES[.,-d]
                set NUM_DIRS=%@FILES[*,d]
                rem echo %ANSI_COLOR_DEBUG%- NUM_FILES == %NUM_FILES .and. NUM_DIRS% == %NUM_DIRS %ANSI_COLOR_RESET%
                if %NUM_DIRS% ne 3                              (goto :No_Collapse)   %+ REM 3 folders really means 1 because "." and ".." 
                if %NUM_FILES eq 0                              (goto :Collapse   )
                if %NUM_FILES eq 1 .and. exist "__ unzipped __" (goto :Collapse   )
                                                                 goto :No_Collapse
                :Collapse
                    %COLOR_REMOVAL%
                    echo      - Collapsing folder...
                    for /a:d /h %folder_to_collapse in (*) do mv/ds "%folder_to_collapse%" .
                    %COLOR_NORMAL%
                :No_Collapse


        rem Leave our mark, and go back to whence we came...
                >"__ unzipped __"
                *cd ..
                popd
    return


:END

echo.
call advice "If we are done processing, install all programs."
call advice "When done, run assimilate-rookie-folders"