@Echo OFF



rem Bypassing pauses is important for automation...
        if %NOPAUSE eq 1 (goto :END)


rem Set window title if instructed:
        if "%PAUSE_WINDOW_TITLE%" ne "" (
                set OLD_TITLE=%@EXECSTR[title]
                title %PAUSE_WINDOW_TITLE%
                set PAUSE_WINDOW_TITLE=
        )


rem Do pauses in the color we want:
        %COLOR_PAUSE%


rem Clear the keyboard buffer to prevent accidental pause-bypasses:
        @input /c /w0 %%just_clearing_the_keyboard_buffer 


rem Preface the pause with an emoji for visual processing ease:
        echos %EMOJI_PAUSE_BUTTON% %ANSI_RESET%``

rem Again, clear the keyboard buffer [/C option] to prevent accidental pause-bypasses:
        *pause /C %@unquote[%*]


rem A pause that doesn't start at the beginning of the line (due to our emoji) doesn't clear itself correctly (TCC bug), so we must do it ourselves:
        echos %ANSI_RESET%%ANSI_EOL%             


rem Bring color & window title back to normal:
        if "%PAUSE_WINDOW_TITLE%" ne "" (set PAUSE_WINDOW_TITLE= %+ title %OLD_TITLE%)


:END

rem 20241028: 🐐 Having some problems Ctrl-Break'ing out of scripts, perhaps adding a slight delay here would help?
        delay /m250


