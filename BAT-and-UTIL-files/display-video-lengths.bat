@Echo  OFF
cls

setdos /x0
call set-tmp-file
call validate-environment-variables FILEMASK_VIDEO TAB TMPFILE
call validate-in-path               ffmpeg


setdos /x-5
echo.
echos %ANSI_BOLD_ON%
echo --------------------------------------------------------------------------------------
echo %italics%%double_underline%HRS%underline_off%%italics_off% %ANSI_BOLD_ON%|%ANSI_BOLD_OFF% %italics%%double_underline%MIN%underline_off%%italics_off% %ANSI_BOLD_ON%|%ANSI_BOLD_OFF%  %italics%%double_underline%SEC%underline_off%%italics_off% %ANSI_BOLD_ON%|%ANSI_BOLD_OFF% %italics%%double_underline%NAME%underline_off%%italics_off%
echo --------------------------------------------------------------------------------------
echos %ANSI_BOLD_OFF%
setdos /x0


rem doing it in order of filesize for now, even though it has little to do with video length, it has more to do with it than an alphabetized list does...
echos %ANSI_SAVE_POSITION
for /o:s %vidfile in (%FILEMASK_VIDEO) gosub dovid %vidfile
echos %ANSI_RESTORE_POSITION
call sort %tmpfile%




goto :END

    :dovid [%vidfile]
        set SECONDS=%@FORMATN[5.0,%@EXECSTR[call display-video-length "%vidfile%"]]
        set MINUTES=%@FORMATN[3.0,%@EVAL[%SECONDS% / 60]]
        set   HOURS=%@FORMATN[1.1,%@EVAL[%MINUTES% / 60]]
        setdos /x-5
            echos %ANSI_ERASE_CURRENT_LINE%                                                                          >>%tmpfile%
            echo %hours% %ANSI_BOLD_ON%|%ANSI_BOLD_OFF% %MINUTES% |%SECONDS %ANSI_BOLD_ON%|%ANSI_BOLD_OFF% %vidfile% >>%tmpfile%
            echo %hours% %ANSI_BOLD_ON%|%ANSI_BOLD_OFF% %MINUTES% |%SECONDS %ANSI_BOLD_ON%|%ANSI_BOLD_OFF% %vidfile% 
        setdos /x0
    return

:END

echo %ANSI_BOLD_ON%--------------------------------------------------------------------------------------%ANSI_BOLD_OFF%

