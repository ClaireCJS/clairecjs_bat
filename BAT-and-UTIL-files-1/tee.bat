@Echo OFF
@on break cancel

if defined TEECOLOR (
    %TEECOLOR%
	unset /q TEECOLOR
)

*tee %*

if defined TEEMESSAGE (
    echo %TEEMESSAGE%
    unset /q TEEMESSAGE
)

