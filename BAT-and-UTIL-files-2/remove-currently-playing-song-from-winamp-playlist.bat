@Echo OFF
@on break cancel


rem UPDATES TO THIS need to also go into determine-currently-playing-playlist-tracknumber.bat  ... for dumb reasons of avoiding maximum batch nesting limits:
        rem TMPPAGE=c:\recycled\wawi-index-%_DATETIME-%_PID.html
        rem TMPPAGE=c:\recycled\wawi-index.html
        set TMPPAGE=%temp%\wawi-index.html

rem DEBUG CONSIDERATIONS:
        if %DEBUG eq 1 (call debug "remove-currently-playing-song-from-playlist.bat  (batch=%_BATCH)")

rem Validate environment (once):
        iff "1" != "%validated_rmCurSongFromWinAmpPlaylist%" then
                call validate-in-path               print-message debug warning removal fatalerror AskYN wget perl get-currently-playing-tracknum-from-wawi-index_html.pl delete-track-from-currently-playing-playlist
                call validate-environment-variables ansi_colors_have_been_set %+ rem don’t validate TMPPAGE because it’s not set yet
                set  validated_rmCurSongFromWinAmpPlaylist=1
        endiff        


rem Delete previous file:
        if not exist %TMPPAGE% goto :TmpPageDoesNotExist
                *del /q %TMPPAGE%
                if exist %TMPPAGE% goto :ERROR_TmpPageWouldNotDelete
        :TmpPageDoesNotExist

rem Get track number from WAWI status page:
        rem c:\cygwin\bin\wget.exe -O%TMPPAGE% http://%TMPMUSICSERVER/main >nul >&>nul
                          wget     -O%TMPPAGE% http://%TMPMUSICSERVER/main >nul >&>nul
        set TRACKNUM=%@EXECSTR[get-currently-playing-tracknum-from-wawi-index_html.pl <%TMPPAGE%]


rem Ask:
        call AskYN "Remove track #%blink_on%%TRACKNUM%%blink_off% from Winamp playlist" yes 30
        if "N" == "%ANSWER%" goto :decided_not_to_remove_from_playlist


rem Remove that track number from the playlist:
        call removal "Removing track %TRACKNUM% from Winamp playlist..."
        delete-track-from-currently-playing-playlist %TRACKNUM% >nul >&>nul


goto :END


        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :decided_not_to_remove_from_playlist
                call warning "Did not remove track %TRACKNUM% from Winamp playlist..."
        goto :END
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

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
