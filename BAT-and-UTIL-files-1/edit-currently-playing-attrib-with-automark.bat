@loadbtm on
@Echo Off
@on break cancel

set AUTOMARK_TEMP=%AUTOMARK%
set AUTOMARKAS_TEMP=%AUTOMARKAS%

    unset /q AUTOMARK
    unset /q AUTOMARKAS
    @edit-currently-playing-attrib %*

set AUTOMARK=%AUTOMARK_TEMP%
set AUTOMARKAS=%AUTOMARKAS_TEMP%

