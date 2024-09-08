@Echo OFF

if "%SLEEPING%" eq "1" goto :Asleep              %+ REM don't speak loud words if spouse is asleep!
                       goto :Awake

    :Asleep                             
        cls
        %COLOR_ALARM%  %+       %+ say   %*      %+ REM write huge banner to screen instead of speaking
        %COLOR_ADVICE% %+ echo. %+ echos %*      %+ REM write normal-sized version too in case banner fails
        %COLOR_NORMAL% %+ echo. %+ delay /m 1000 %+ REM wait a second afterward
    goto :END


    :Awake
        rem Method 1: speak.exe %*                            %+ REM Just speak normally if no one is sleeping
        rem Method 2: more reliable: mshta vbscript:Execute("CreateObject(""SAPI.SpVoice"").Speak(""%*"")(window.close)")

        rem Method 3: 2024 new replacement which works through ALL sound devices simultaneously which is pretty amazing:
        call validate-in-path wsay
        wsay "%@UNQUOTE[%*]" --volume 100 --voice 3 --playback_device all --speed 55


        rem The voices I had when I set this to 3 (Zira):
            rem C:\>wsay -l
            rem  1 : Microsoft David Desktop - English (United States)
            rem  2 : Microsoft Hazel Desktop - English (Great Britain)
            rem  3 : Microsoft Zira Desktop - English (United States)
            rem  4 : Microsoft David - English (United States)
            rem  5 : Microsoft James - English (Australia)
            rem  6 : Microsoft Linda - English (Canada)
            rem  7 : Microsoft Richard - English (Canada)
            rem  8 : Microsoft George - English (United Kingdom)
            rem  9 : Microsoft Hazel - English (United Kingdom)
            rem 10 : Microsoft Susan - English (United Kingdom)
            rem 11 : Microsoft Sean - English (Ireland)
            rem 12 : Microsoft Heera - English (India)
            rem 13 : Microsoft Ravi - English (India)
            rem 14 : Microsoft Catherine - English (Australia)
            rem 15 : Microsoft Mark - English (United States)
            rem 16 : Microsoft Zira - English (United States)


    goto :END

:END
