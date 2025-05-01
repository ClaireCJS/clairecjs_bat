@Echo OFF

if "%1" == "on"  .or. "%1" == "" gosub on
if "%1" == "off"                 gosub off

goto :END

        :on []
                set LYRIC_KARAOKE_ALIGNMENT_THOROUGH_MODE=1
        return

        :off []
                set LYRIC_KARAOKE_ALIGNMENT_THOROUGH_MODE=0
        return

:END


