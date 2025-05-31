@on break cancel
@Echo OFF


:REQUIRES: environm.btm (to set %FILEMASK_AUDIO% environment variable), validate-file-extension.bat (to validate parameters), EnqueueEE.exe

:::::::::::::::: BUT WHAT ABOUT REGEXES? Use the other enqueue bat file that is regex related



rem Validate environment (once):
        iff "%ENQ_ENV_VALIDATED%" != "1" then
                call validate-in-path EnqueueEE.exe
                set ENQ_ENV_VALIDATED=1
        endiff



rem Make sure the file we want to enqueue actually exists:
        if exist %1 goto :File_Exists_so_lets_do_the_thing
                    %COLOR_ALARM%     %+ echo FATAL ERROR: %1 Doesn’t exist! %+ echo.
                    %COLOR_IMPORTANT% %+ echo - %0.bat is not meant for regular expressions btw %+ echo.
                    %COLOR_ADVICE%    %+ echo * This can no longer enqueue regular expressions; use mplay for that: %+ echo.
                    %COLOR_ADVICE%    %+ echo      mplay {regex} - pauses main player and runs playlist matching regex in a secondary player
                    beep
                    beep
                    beep
                    goto :END
        :File_Exists_so_lets_do_the_thing

rem Validate the extension of the file:
        rem old if "%@EXT[%1]" == "lrc" (call error "nono on lrc files" %+ goto :END)
        call validate-file-extension %1 %FILEMASK_AUDIO%


rem Unpause the music otherwise EnqueueEE.exe won’t work:
    if "%_PBATCHNAME%" != "" (%COLOR_NORMAL% %+ echo.)
    call unpause
    if %DEBUG% gt 0 call print-if-debug "EnqueueEE.exe -a “%italics%%@UNQUOTE[%@LFN[%1]]%italics_off%”"


rem Enque the track into winamp w/EnqueueEE.exe:
    rem %@ANSI_RGB_FG[255,200,200]EnqueueEE.exe -a "%@UNQUOTE[%@LFN[%1]]"
              echo %@randFG_soft[]EnqueueEE.exe -a "%@UNQUOTE[%@LFN[%1]]"
                                  EnqueueEE.exe -a "%@UNQUOTE[%@LFN[%1]]"




:END

