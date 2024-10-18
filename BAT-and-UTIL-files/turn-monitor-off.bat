@Echo OFF

:::: PHYSICAL CONSIDERATIONS:
    echo.
    echo.
    echo.
    echo.
    echo.
    %COLOR_PROMPT% %+ echos  *** TURN MOUSE UPSIDE-DOWN! *** `` %+ %COLOR_NORMAL% %+ echo.
    sleep 5


::::: TURN THE MONITORS OFF:
    title Running nircmd.exe monitor off
            start nircmd.exe monitor off
    title Nircmd done


::::: ADVICE/CLEANUP:
    %COLOR_UNIMPORTANT% %+ echo * moff-old for older 2000s-era moff script %+ %COLOR_NORMAL%
    call fix-window-title

