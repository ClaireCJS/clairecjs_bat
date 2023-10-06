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
        speak.exe %*                            %+ REM Just speak normally if no one is sleeping
    goto :END

:END
