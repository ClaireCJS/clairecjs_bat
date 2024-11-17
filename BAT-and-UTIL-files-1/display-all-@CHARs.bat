@Echo OFF


set DELAY_MS=1 %+ rem how many ms to delay between each char

set i=1
:infinite_loop
    if %i eq 157 .or.  %i eq 158 .or.  %i eq 159 (
        echo %%@CHAR[ %i ] == {skipped: undisplayable}
    ) else (
        echo %%@CHAR[ %i ] == %@CHAR[%i]
        rem quick: echos %@CHAR[%i]
    )
    set i=%@EVAL[%i+1]   
    delay /m %DELAY_MS%                             
goto :infinite_loop

