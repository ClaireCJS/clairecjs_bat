@Echo on
 on break cancel
set PARAM_1=%1
*start "" ms-settings:apps-volume
if "%PARAM_1" eq "exitafter" (exit)
