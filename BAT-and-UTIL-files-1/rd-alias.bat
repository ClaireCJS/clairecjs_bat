@Echo Off
@on break cancel

rem Figure out which argument is the folder:
        repeat 20 if isdir %[%_repeat] set RD_FOLDER=%[%_repeat]

rem Get the FULL path of that folder:
        if "%rd_folder_full%" != "" (set RD_FOLDER_FULL=%@FULL[%RD_FOLDER])

rem Remove any FILE_COUNT environment variables (used in cd.bat) related to this folder:
        unset /q file_count_*%RD_FOLDER_FULL%*










rem the rest is on line 69 because that way if there is an error, it's line 69... which is pretty funny












































rem Are there files in the folder we’re trying to remove?
        iff isfile "%@UNQUOTE[%*]\*" then
                echo.
                echos %ANSI_COLOR_BRIGHT_RED%%STAR% ERROR! Folder “%italics_on%%1%italics_off%” still has files in it!
                echo.
        endiff
        goto :END

rem Actually do the removing :) we add /Nt to skip updating JPSTREE.IDX file in order to achive a neglible speed increase
rem TCC v32 introduced /Nj to not follow symlinks option
        rem *rd /Nt  %*
            *rd /Ntj %*



:END

