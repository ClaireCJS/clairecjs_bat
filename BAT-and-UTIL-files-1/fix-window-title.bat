@Echo OFF
:Echo on

:ASSUMES: detect-command-line-container has been called to set %container

goto :%OS
goto :default

    :default
    :Windows_NT
    :7
    :10
    :11
    :2K
    :XP
    :NT
        set WINDOW_TITLE_TO_SET=TCC
    goto :Title_It


    :95
    :98
    :ME
        set WINDOW_TITLE_TO_SET=4DOS
    goto :Title_It

:Title_It

    if "%TASK%" ne "" (set WINDOW_TITLE_TO_SET=%@UNQUOTE[%TASK%])

    REM  call set-window-title  "%WINDOW_TITLE_TO_SET%"
         call set-window-title  "%WINDOW_TITLE_TO_SET%"


