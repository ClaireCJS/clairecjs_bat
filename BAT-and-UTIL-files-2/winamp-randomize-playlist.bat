@echo off
 on break cancel

if "%MACHINENAME%" == "%MUSICSERVERMACHINENAME%" (goto :IsMusicServer)

rem old 2006 Upstairs/Downstairs flip scenario settings: call setTmpMusicServer.bat %*

::::: CONFIGURATION:
    set DELAY=delay /m 200



::::: SWITCH PLAYLIST USING GIRDER:
    rem NOTE TO GITHUB FOLKS: copy of my girder configuration files can be found as girder.gml
    call validate-girder-is-running
    call validate-environment-variables        MUSICSERVERIPONLY  GIRDERPORT  GIRDERPASSWORD 
    set  COMMAND=girder-internet-event-client %MUSICSERVERIPONLY %GIRDERPORT %GIRDERPASSWORD RANDOMIZE whatever
         
::::: Randomize 4 times... for some reason
       %COLOR_DEBUG% %+ echo Command is: %COMMAND%
           %COMMAND% %+ %DELAY%
           %COMMAND% %+ %DELAY%
       rem %COMMAND% %+ %DELAY%
       rem %COMMAND% %+ %DELAY%

    :: some 2005-2009 stuff: if "%@UPPER[%MACHINENAME%]" eq "HADES" goto :HadesGirderIsBroken



goto :END


        ::::: some 2005-2009 stuff?
            :HadesGirderIsBroken
                ::::: This part works for local machines only:
                echo on
                    call change-command-separator-character-to-tilde.bat >nul
							:IsMusicServer
							if exist      "%ProgramFiles\Winamp\winamp.exe" set WINAMP="%ProgramFiles\Winamp\winamp.exe"
							if exist "%ProgramFiles(x86)\Winamp\winamp.exe" set WINAMP="%ProgramFiles(x86)\Winamp\winamp.exe"
							if exist            "%UTIL2%\Winamp\winamp.exe" set WINAMP="%UTIL2%\Winamp\winamp.exe"
                            LaunchKey.exe "^{TAB}+^R^{TAB}+^R" %WINAMP
                            rem 20231111 this made 2 winamps: LaunchKey.exe "^{TAB}+^R^{TAB}+^R" %WINAMP
							call bring-back-focus
                    call change-command-separator-character-to-normal >nul
                echo off
            goto :END


:END
