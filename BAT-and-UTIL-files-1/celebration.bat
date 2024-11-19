@Echo OFF
 on break cancel

set MSG=%*
if "%1" eq "" set MSG=*** Success!!! ***

call print-message celebration %MSG%
