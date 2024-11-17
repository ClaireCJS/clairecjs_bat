REM @Echo OFF

set ORIG_TITLE=%_WINTITLE
set PID=%_PID

set    NEW_TITLE=!!MOVE%PID%!!
title %NEW_TITLE%

set TO_ACTIVATE=%PID%
set TO_ACTIVATE=*%PID%*
set TO_ACTIVATE=*%NEW_TITLE%*


delay /m 50
REM pause
REM way too big!

REM i think the scaling change between monitors makes these REALLY GOOD NUMBERS not work when used from a diff monitor:
REM activate %TO_ACTIVATE% pos=-1339,-1079,1290,672
    activate %TO_ACTIVATE% pos=-1339,-1079,851,403

title     %ORIG_TITLE
