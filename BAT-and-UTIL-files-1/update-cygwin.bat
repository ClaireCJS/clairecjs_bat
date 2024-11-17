@echo off

call warning "This BAT file $0 is neutered because it's been tried, and turned out to be so incredibly damaging to cygwin without regression testing"
call warning "and regression testing it all is beyond my personal scope!"
echo warning "But if you really want to know how to update-cygwin, it's like this:"

echo.

echo cdd C:\cygwin
echo echo yr|copy https://www.cygwin.com/setup-x86_64.exe
echo setup-x86_64.exe -q -g
