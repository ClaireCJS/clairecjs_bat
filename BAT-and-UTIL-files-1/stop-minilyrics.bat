@Echo Off


    echo.
    echo.
    call important "Killing MiniLyrics..."
    rem call killIfRunning  MiniLyrics  MiniLyrics
    kill /f minilyrics* >&>nul
