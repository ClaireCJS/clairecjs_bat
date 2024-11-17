@echo off
:: Read each line from the file and echo it to the console
for /f "usebackq delims=" %%a in ("color_cycle_output.txt") do (
    echos %%a
    :: Adjust the sleep time as needed
    delay /m 1
)
echos %ANSI_RESET%