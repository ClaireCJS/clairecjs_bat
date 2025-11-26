@Echo OFF

:DESCRIPTION: Deletes a folder IF it exists.


set DIR=%@UNQUOTE[%1]

if isdir "%DIR%" call deltree "%DIR%"

