@Echo Off

rem Stop user from doing this if it's our music server!

        iff "%MachineName%" eq "%MusicServerMachineName%" then
                call warning   "We do NOT want to run this on our musicserver!"
                call error     "Better not run this on this machine!"
                call warning   "Sorry, not running this even if you want me to!"
                call exit-maybe
                goto :END
        endiff

echo %ANSI_COLOR_ERROR% Serously. Not running it.
cancel

