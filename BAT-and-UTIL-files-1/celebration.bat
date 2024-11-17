@Echo OFF

set MSG=%*
if "%1" eq "" set MSG=*** Success!!! ***

call print-message celebration %MSG%
