@Echo off

set USB_DRIVE=X
if "%1" ne "" .and. "%@READY[%1]" eq "1" (set USB_DRIVE=%1)

call validate-in-path drives RemoveDrive.exe
call validate-environment-variables COLOR_PROMPT COLOR_INPUT COLOR_NORMAL

cls
call drives

%COLOR_PROMPT% %+ echos Which drive letter (no colon)? %+ %COLOR_NORMAL% %+ echo.
%COLOR_INPUT%  %+ eset USB_DRIVE
RemoveDrive.exe %USB_DRIVE%

set LAST_USB_DRIVE_REMOVED=%USB_DRIVE%