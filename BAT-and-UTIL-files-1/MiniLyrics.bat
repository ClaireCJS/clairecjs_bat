@Echo OFF
 on break cancel

call validate-in-path isRunning.bat warning_less.bat askYN.bat taskend important_less.bat start-minilyrics.bat

set THING=MiniLyrics

call isRunning %THING% quiet
:Recheck
iff %isRunning eq 1 then
        call warning_less "%THING% is already running!"
        call advice   "Run '%0 restart' if you want to kill it and restart it"
        call askYN    "Want me to go ahead and restart MiniLyrics?" No 4
        iff %DO_IT eq 1 then
                taskend /f %THING%
                call isRunning %THING% 
                goto :Recheck
        endiff
else 
        call important_less "Running %THING% via start-minilyrics.bat"
        call start-minilyrics.bat

endiff

