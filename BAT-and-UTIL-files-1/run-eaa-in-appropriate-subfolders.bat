@Echo off

rem AUDIO PROCESING WORKFLOW: Tool used to extract album art from the first file in a folder, 
rem                           compare it to existing cover.jpg files, and if it is a larger resolution, 
rem                           replace the existing cover.jpg with the extracted cover.jpg


rem USAGE:
        if "%1" eq "TEST"  (goto :Parametered)
        if "%1" eq "FORCE" (goto :Parametered)

                :No_Parameters_Given
                    %COLOR_WARNING%
                        echo ***** THIS IS ONLY TO BE USED DURING AUDIO PROCESSING WORKFLOW! *****
                        echo *** IT COULD BE VERY DESTRUCTIVE TO RUN IT IN ANY OTHER CONTEXT! ****
                        echo.
                        echo *** TYPE %0 TEST  TO TEST WHAT   WILL   HAPPEN ***
                        echo *** TYPE %0 FORCE TO MAKE THIS ACTUALLY HAPPEN ***
                goto :END


rem VALIDATE ENVIRONMENT:
        call validate-environment-variable FILEMASK_AUDIO
        call validate-in-path extract-cover_art-from-first-found-audio-file.bat run-eaa-in-appropriate-subfolders.bat eaa-if-appropriate-for-workflow.bat eaa.bat extract-cover_art-from-first-found-audio-file.bat fix-wrong-image-extensions wait.bat


rem PASS PARAMETER IF PROPERLY USED:
        :Parametered
        if "%1" eq "FORCE" (sweep call eaa-if-appropriate-for-workflow.bat FORCE)
        if "%1" eq "TEST"  (sweep call eaa-if-appropriate-for-workflow.bat TEST )


:END
