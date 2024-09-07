@Echo OFF

rem Get paramters:
        if "%1" eq "" (goto :usage)
        set FOLDER_TO_DEP_IN=%@UNQUOTE[%1]
        call validate-environment-variable FOLDER_TO_DEP_IN 

rem Check each file, dep if exists in FOLDER_TO_DEP_IN:
    for /a: /h %%tmpFile in (*) do   if exist "%FOLDER_TO_DEP_IN%\%tmpFile" (echos %@RANDFG_SOFT[] %+ call deprecate "%FOLDER_TO_DEP_IN%\%tmpFile")


goto :END

        :usage
            %COLOR_ADVICE%
            echo USAGE: deprecate-files-in-other-folder-if-they-have-the-same-name-as-files-in-this-folder.bat {other_folder} 
        goto :END

:END