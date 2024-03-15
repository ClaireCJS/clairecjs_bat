@Echo OFF



rem Bypassing pauses is important for automation...
        if %NOPAUSE eq 1 (goto :END)


rem Do pauses in the color we want
        %COLOR_PAUSE%


rem Clear the keyboard buffer to prevent accidental pause-bypasses
        @input /c /w0 %%just_clearing_the_keyboard_buffer 


rem Preface the pause with an emoji for visual processing ease:
        echos %EMOJI_PAUSE_BUTTON% ``

rem Again, clear the keyboard buffer [/C optoin] to prevent accidental pause-bypasses:
        *pause %* /C 


rem A pause that doesn't start at the beginning of the line (due to our emoji) doesn't clear itself correctly (TCC bug), so we must do it ourselves:
        echos %ANSI_ERASE_CURRENT_LINE%             


rem Bring color back to normal:
        %COLOR_NORMAL%



:END
