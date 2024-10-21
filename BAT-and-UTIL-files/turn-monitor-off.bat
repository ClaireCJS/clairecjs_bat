@Echo OFF

rem Validate environment:
        call validate-in-path nircmd.exe fix-window-title warning error exit-maybe


rem Stop user from doing this if it's our music server!
        iff "%MachineName%" eq "%MusicServerMachineName%" then
                call warning   "We do NOT want to run this on our musicserver! It kills the music and makes it hard to start!"
                call error     "Better not run this on this machine!"
                call warning   "Sorry, not running this even if you want me to!"
                call exit-maybe
                goto :END
        endiff


rem PHYSICAL CONSIDERATIONS:
        repeat 5 echo.
        call warning "TURN MOUSE UPSIDE-DOWN"
        call wait 5 "(turn mouse upside-down)"


:rem TURN THE MONITORS OFF:
        title Running nircmd.exe monitor off
                rem start nircmd.exe monitor off
        title Nircmd done


:rem ADVICE/CLEANUP:
        call unimportant "run '%italics_on%moff-old%italics_off%' from the OBSOLETE SCRIPTS archive for older 2000s-era monitors-off script "
        call fix-window-title

:END
