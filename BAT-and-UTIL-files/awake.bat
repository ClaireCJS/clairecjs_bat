@echo off

set SLEEPING=0

if defined EMOJI_EGG .and. defined EMOJI_BACON (
    echo.
    echo Wakey Wakey! Eggs and bakey!
    call bigecho %EMOJI_EGG%%EMOJI_BACON%
)

if 1 ne %X10_DOWN (call b1 on)
