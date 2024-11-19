@echo off
 on break cancel

rem UPDATES TO THIS need to also go into remove-currently-playing-song-from-playlist.bat ... for dumb reasons of avoiding maximum batch nesting limits:
        rem TMPPAGE=c:\recycled\wawi-index-%_DATETIME-%_PID.html
        rem TMPPAGE=c:\recycled\wawi-index.html
        set TMPPAGE=%temp%\wawi-index.html




:Again
if exist %TMPPAGE% (*del /q %TMPPAGE%)
if exist %TMPPAGE% (goto :ERROR_TmpPageWouldNotDelete %+ goto :Again)
wget -O%TMPPAGE% http://%TMPMUSICSERVER/main >nul >&>nul
call get-currently-playing-tracknum-from-wawi-index_html.pl <%TMPPAGE%






goto :END

	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	:ERROR_TmpPageWouldNotDelete
		call FATALERROR "%TMPPAGE% would not delete, and needs to be deleted to run this"
	goto :END
	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


:END
