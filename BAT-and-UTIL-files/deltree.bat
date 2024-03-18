@Echo OFF

set DIR=%1

rem Make sure folder exists
    if not isdir %DIR (
        call error "directory '%DIR%' does not exist"
    )



if isdir %DIR% (
    call askyn "%EMOJI_NO_ENTRY% Delete folder '%italics%%@UNQUOTE[%DIR]%%italics_off%' %blink%%underline%completely%underline_off%%blink_off%" no
    if %ANSWER eq Y (
        %COLOR_REMOVAL% 
        echo. 
        echo %EMOJI_NO_ENTRY%%EMOJI_NO_ENTRY%%EMOJI_NO_ENTRY%%EMOJI_NO_ENTRY%%EMOJI_NO_ENTRY%%EMOJI_NO_ENTRY%%EMOJI_NO_ENTRY%%ITALICS_ON%%FAINT_ON%``
        echo r | *del /a: /f /k /s /t /x /z /Nj /P /E %DIR%
        echo %ITALICS_OFF%%FAINT_OFF%%EMOJI_NO_ENTRY%%EMOJI_NO_ENTRY%%EMOJI_NO_ENTRY%%EMOJI_NO_ENTRY%%EMOJI_NO_ENTRY%%EMOJI_NO_ENTRY%%EMOJI_NO_ENTRY%``
    )
)



rem Currently not implemented, but reset this just to be safe:
    if %AUTO_DEL_DIR eq 1 (set AUTO_DEL_DIR=0)


