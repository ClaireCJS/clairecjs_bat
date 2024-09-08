@echo off

if "%MACHINENAME%" eq "THAILOG" (goto :Thailog)




    :Default
        call pf
        cd Google
        cd Chrome
        cd Application
        start chrome.exe
    goto :END




    :Thailog
        call nocar
        unset /q CHROMEARGS
            :TEMPFIX: if "%MACHINENAME%" eq "THAILOG" (set CHROMEARGS=--user-data-dir=c:\ChromeUserDataThailog2019\)
            start %@SFN["%[ProgramFiles(x86)]%\Google\Chrome\Application\chrome.exe"] %CHROMEARGS%  %*
        unset /q CHROMEARGS
    goto :END





:END

