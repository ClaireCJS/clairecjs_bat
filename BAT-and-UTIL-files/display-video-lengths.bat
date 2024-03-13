@Echo  OFF

setdos /x0
call validate-environment-variable FILEMASK_VIDEO TAB
call validate-in-path              ffmpeg


setdos /x-5
echo.
echo --------------------------------------------------------------------------------------
echo HRS%tab% | MIN%tab% |  SEC%tab% | NAME
echo --------------------------------------------------------------------------------------
setdos /x0


rem doing it in order of filesize for now, even though it has little to do with video length, it has more to do with it than an alphabetized list does...
for /o:s %vidfile in (%FILEMASK_VIDEO) gosub dovid %vidfile




goto :END

    :dovid [%vidfile]
        set SECONDS=%@FORMATN[5.0,%@EXECSTR[call display-video-length "%vidfile%"]]
        set MINUTES=%@FORMATN[3.0,%@EVAL[%SECONDS% / 60]]
        set   HOURS=%@FORMATN[1.1,%@EVAL[%MINUTES% / 60]]
        setdos /x-5
        echo %hours%%tab% | %MINUTES%%tab% |%SECONDS%%tab% | %vidfile%
        setdos /x0
    return

:END

echo --------------------------------------------------------------------------------------

