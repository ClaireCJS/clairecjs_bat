@echo off

 
 unset /q OUR_CHROMEARGS




rem EXAMPLE: How to specify a different data folder for one machine: 
rem                 if "%MACHINENAME%" eq "THAILOG" (set OUR_CHROMEARGS=--user-data-dir=c:\ChromeUserDataThailog2019\)



    :Default
            call validate-in-path programfiles.bat
            call                  programfiles.bat
            if not isdir      Google (call error "no %italics_on%Google%italics_off%%zzz% folder in %italics_on%%_CWP%italics_off% while running %italics_on%$0%italics_off%" %+ goto :END)
            cd                Google
            if not isdir      Chrome (call error "no %italics_on%Chrome%italics_off%%zzz% folder in %italics_on%%_CWP%italics_off% while running %italics_on%$0%italics_off%" %+ goto :END)
            cd                Chrome
            if not isdir Application (call error "no %italics_on%Application%italics_off% folder in %italics_on%%_CWP%italics_off% while running %italics_on%$0%italics_off%" %+ goto :END)
            cd           Application
            if not exist  chrome.exe (call error "no %italics_on%chrome.exe %italics_off%  file  in %italics_on%%_CWP%italics_off% while running %italics_on%$0%italics_off%" %+ goto :END)
            start         chrome.exe %OUR_CHROMEARGS%  %*
    goto :END




:END

