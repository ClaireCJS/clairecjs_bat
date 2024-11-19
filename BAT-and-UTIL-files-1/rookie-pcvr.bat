@echo off
@on break cancel
cls
echo.
call validate-environment-variable ROOKIE
%ROOKIE%
echo %star% %bold%%ansi_bg_green% Last run on: %ansi_reset% %star%%blink_on% %+ echos    %ANSI_BG_GREEN% %+ dg " 0.*__.last.run"|strip-ansi|sed -e "s/[0-9][0-9]*:.*$/ %ANSI_RESET%/"
echo.
call warning "Take note of this date"
call warning "don't run this unless you're ready to download the new stuff"
call warning "When done downloading, run process-rookie-folders to extract"
call warning "When done extracting , install each game"
call warning "When done installing , run assimilate-rookie-folders"
echo.
pause
pause
pause
>"__ last run as of timestamp of this file __"
rem start "PCVR-Rookie v1.4.exe"
    start "PCVR-Rookie v1.5.exe"
%ROOKIE%
