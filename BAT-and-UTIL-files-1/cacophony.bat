
set NOISE_TIME=5 %+ if "%1" ne "" set NOISE_TIME=%1

for /l %count in (1,1,10) start "cacophony" /INV white-noise  %NOISE_TIME% exitafter

