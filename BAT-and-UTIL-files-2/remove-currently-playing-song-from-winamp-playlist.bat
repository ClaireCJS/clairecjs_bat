@Echo OFF
@on break cancel



rem UPDATES TO THIS need to also go into determine-currently-playing-playlist-tracknumber.bat  ... for dumb reasons of avoiding maximum batch nesting limits:
        rem TMPPAGE=c:\recycled\wawi-index-%_DATETIME-%_PID.html
        rem TMPPAGE=c:\recycled\wawi-index.html
        set TMPPAGE=%temp%\wawi-index.html


rem DEBUG CONSIDERATIONS:
    if %DEBUG eq 1 (call debug "remove-currently-playing-song-from-playlist.bat  (batch=%_BATCH)")

rem Delete previous file:
        if exist %TMPPAGE% (*del /q %TMPPAGE%)
        if exist %TMPPAGE% (goto :ERROR_TmpPageWouldNotDelete)

rem Get track number from WAWI status page:
        rem c:\cygwin\bin\wget.exe -O%TMPPAGE% http://%TMPMUSICSERVER/main >nul >&>nul
                          wget     -O%TMPPAGE% http://%TMPMUSICSERVER/main >nul >&>nul
        set TRACKNUM=%@EXECSTR[get-currently-playing-tracknum-from-wawi-index_html.pl <%TMPPAGE%]

rem Remove that track number from the playlist:
        call removal "Removing track %TRACKNUM% from Winamp playlist..."
        delete-track-from-currently-playing-playlist %TRACKNUM% >nul >&>nul


goto :END

        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :ERROR_NoTrackNum
                call  FATALERROR "Remove-currently-playing-song-from-playlist failed because TRACKNUM was not retrieved..."
        goto :END
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :ERROR_TmpPageWouldNotDelete
                call FATALERROR "%TMPPAGE% would not delete, and needs to be deleted to run this"
        goto :END
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:END
