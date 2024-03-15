@echo off

if %NOPAUSE eq 1 goto :END

        %COLOR_PAUSE%

            @input /c /w0 %%just_clearing_the_keyboard_buffer 
            echos %EMOJI_PAUSE_BUTTON% ``
            *pause %* /C 

        %COLOR_NORMAL%

:END
