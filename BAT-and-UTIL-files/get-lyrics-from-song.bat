@Echo off

rem GETTER=get-lrc-with-lyricy.bat —— was awful because only took filename into account
set GETTER=get-lyrics-with-lyricsgenius.bat

call validate-in-path %GETTER%

    call %GETTER% %*

