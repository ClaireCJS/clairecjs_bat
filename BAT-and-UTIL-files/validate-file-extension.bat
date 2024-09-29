@Echo OFF

rem USAGE:   call validate-file-extension [filename]   [extension(s)]           //%FILEMASK_{type} env vars work!  "*.txt;*.bat" works. "txt bat" works too.
rem EXAMPLE: call validate-file-extension filename.txt txt                      //example to check for one  extension
rem EXAMPLE: call validate-file-extension %FILENAME%   "txt text rtf html"      //example to check for many extensions


rem SETUP: Get Parameters
    set VALIDATION_FILE=%1
    set  EXTENSION_LIST=%2

rem USAGE if no parameters:
    if "%1" eq "" (
        echo.
        call important_less "USAGE: $0 {filename} {extension(s)}"
        echo.
        %COLOR_ADVICE% %+ echo EXAMPLE: $0 %%FILENAME  txt
        %COLOR_ADVICE% %+ echo EXAMPLE: $0 %%FILENAME "txt text rtf html"
        %COLOR_ADVICE% %+ echo EXAMPLE: $0 %%FILENAME *.txt;*.rtf;*.html
        goto :END
    )

rem SETUP: Validate parameters
    call validate-env-var VALIDATION_FILE skip_validation_existence
    if not defined EXTENSION_LIST (call error "your second parameter to %0 needs to be an extension or list of extensions but was instead '%EXTENSION_LIST%'")

rem MESSAGE: Message extension parameters because our filemask env vars are usually "*.txt;*.lst" and we need "txt lst"
    set  EXTENSION_LIST_TO_USE=%@REPLACE[*.,,%@REPLACE[;, ,%EXTENSION_LIST%]]
    REM echo EXTENSION_LIST_TO_USE is '%EXTENSION_LIST_TO_USE%'

rem VALIDATE: Check each extension in extension list and see if it matches our file
    set VALIDATION_FILE_EXT=%@UNQUOTE[%@EXT[%VALIDATION_FILE]]
    for %tmp_extension in (%EXTENSION_LIST_TO_USE) do (
        if %DEBUG gt 0 (call debug "- checking if extension '%tmp_extension%' applies to file '%VALIDATION_FILE%' which has VALIDATION_FILE_EXT='%VALIDATION_FILE_EXT'-- test:if '%@EXT[%VALIDATION_FILE]' eq '%tmp_extension' goto :Validated_File_Extension_Successfully")
        if "%VALIDATION_FILE_EXT" eq "%@UNQUOTE[%tmp_extension]" (
            set VALIDATED_EXTENSION_LAST_VALUE=1
            goto :Validated_File_Extension_Successfully
        ) else (
            set VALIDATED_EXTENSION_LAST_VALUE=0
        )
    )

rem ERROR: At this point, all checks have failed and the file is not valid!
    call error "*** Validation of file '%VALIDATION_FILE%' failed because it's extension is not one of: '%italics%%underline%%EXTENSION_LIST_TO_USE%%italics_off%%underline_off%'"

:Validated_File_Extension_Successfully

:END
