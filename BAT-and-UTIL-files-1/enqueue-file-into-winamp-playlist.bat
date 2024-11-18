@Echo OFF


:REQUIRES: environm.btm (to set %FILEMASK_AUDIO% environment variable), validate-file-extension.bat (to validate parameters), EnqueueEE.exe

:::::::::::::::: tODO
:::::::::::::::: THIS WORKS FOR BOTH M3U AND MP3 FILES!!!!!!!
:::::::::::::::: BUT WHAT ABOUT REGEXES?
:::::::::::::::: IF IT IS A FILE THAT DOESN'T EXIST, THEN WE NEED TO MCHK IT INTO A TEMP PLAYLIST, AND ENQUEUE THAT!
:::::::::::::::: BUT ALSO CHECK IF THEPLAYLIST LENGTH IS 0!!!!!



rem Validate environment
    iff %ENQ_ENV_VALIDATED ne 1 then
        call validate-in-path EnqueueEE.exe
        set ENQ_ENV_VALIDATED=1
    endiff




if exist %1 goto :File_Exists_so_lets_do_the_thing

    %COLOR_ALARM%     %+ echo FATAL ERROR: %1 Doesn't exist! %+ echo.
    %COLOR_IMPORTANT% %+ echo - %0.bat is not meant for regular expressions btw %+ echo.
    %COLOR_ADVICE%    %+ echo * This can no longer enqueue regular expressions; use mplay for that: %+ echo.
    %COLOR_ADVICE%    %+ echo      mplay {regex} - pauses main player and runs playlist matching regex in a secondary player
    beep
    beep
    beep
    goto :END



:File_Exists_so_lets_do_the_thing

    rem Validate the extension
        rem old if "%@EXT[%1]" == "lrc" (call error "nono on lrc files" %+ goto :END)
        call validate-file-extension %1 %FILEMASK_AUDIO%

    %COLOR_NORMAL% %+ echo.
    call unpause
    call print-if-debug "EnqueueEE.exe -a '%italics%%@UNQUOTE[%@LFN[%1]]%italics_off%'"
    echo %@ANSI_RGB_FG[255,200,200]EnqueueEE.exe -a "%@UNQUOTE[%@LFN[%1]]"
    rem seems tob e working well nowpause
                                   EnqueueEE.exe -a "%@UNQUOTE[%@LFN[%1]]"







:END

