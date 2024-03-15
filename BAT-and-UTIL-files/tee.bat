@echo off

if defined TEECOLOR (
	%TEECOLOR%
	set TEECOLOR=
)

*tee %*

if defined TEEMESSAGE (
    echo %TEEMESSAGE%
    set TEEMESSAGE=
)
