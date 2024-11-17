@Echo off

rem Go to the internet metronome unless a number is given:
        iff "%1" eq "" then
                echo %ANSI_COLOR_WARNING%Because we did not give a number of seconds to wait in between beeps, we will be going to the internet metronome instead%ANSI_COLOR_NORMAL%
                https://www.metronomeonline.com
                goto :END
        endiff



rem Silly semi-metronome not as good as internet one:
            :top
                echos %@RANDCURSOR[]
                call sleep %1
                echos %@RANDCURSOR[]
                call beep
                echos %@RANDCURSOR[]
            goto :top
            echos %cursor_reset%


:END