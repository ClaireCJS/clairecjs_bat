@loadbtm on
@Echo Off
@on break cancel

rem USAGE:   call validate-file-extension [filename]   [extension(s)]           //%FILEMASK_{type} env vars work!  "*.txt;*.bat" works. "txt bat" works too.
rem EXAMPLE: call validate-file-extension filename.txt txt                      //example to check for one  extension
rem EXAMPLE: call validate-file-extension %FILENAME%  "txt text rtf html"       //example to check for many extensions


rem SETUP: Get Parameters
        set         PARAM_1=%1
        set VALIDATION_FILE=%1
        set  EXTENSION_LIST=%2
        set  CUSTOM_ERR_MSG=%3

rem USAGE if no parameters:
if "%1" == "" (
        echo.
                call important_less "USAGE: $0 {filename} {extension(s)}"
        echo.
        %COLOR_ADVICE% 
                echo EXAMPLE: $0 %%FILENAME   txt                %DASH% simple check of if %%FILENAME%% is a .txt file
                echo EXAMPLE: $0 %%FILENAME *.txt "Not text!"    %DASH% can add a custom error message
                echo EXAMPLE: $0 %%FILENAME  "txt text rtf html" %DASH% can separate multiple extensions by space
                echo EXAMPLE: $0 %%FILENAME *.txt;*.rtf;*.html   %DASH% can separate multiple extensions by semicolon
                echo EXAMPLE: $0 %%FILENAME *.txt;*.rtf;*.html "Manifest file must be TXT, RTF, or HTML" %DASH% can combine functionality
        goto :END
)

rem INIT: See if 1ˢᵗ parameter is environment variable or not:
        if defined %PARAM_1% set VALIDATION_FILE=%[%PARAM_1]
      

rem INIT: Validate parameters
        if not defined VALIDATION_FILE (call fatal_error "1ˢᵗ parameter (validation_file) not provided!" %+ goto :END)
        if not defined EXTENSION_LIST  (call fatal_error "your second parameter to %0 needs to be an extension or list of extensions but was instead “%EXTENSION_LIST%”" %+ goto :END)

rem MESSAGE: Message extension parameters because our filemask env vars are usually "*.txt;*.lst" and we need "txt lst"
        set  EXTENSION_LIST_TO_USE=%@REPLACE[*.,,%@REPLACE[;, ,%EXTENSION_LIST%]]
        REM echo EXTENSION_LIST_TO_USE is “%EXTENSION_LIST_TO_USE%”

rem VALIDATE: Actually Check each extension in extension list and see if it matches our file
        set VALIDATION_FILE_EXT=%@UNQUOTE[%@EXT[%VALIDATION_FILE]]
        for %tmp_extension in (%EXTENSION_LIST_TO_USE) do (
                if %DEBUG gt 0 (call debug "- checking if extension “%tmp_extension%” applies to file “%VALIDATION_FILE%” which has VALIDATION_FILE_EXT=“%VALIDATION_FILE_EXT”-- test:if “%@EXT[%VALIDATION_FILE]” == “%tmp_extension” goto :Validated_File_Extension_Successfully")
                if "%VALIDATION_FILE_EXT" == "%@UNQUOTE[%tmp_extension]" (
                        set VALIDATED_EXTENSION_LAST_VALUE=1
                        goto :Validated_File_Extension_Successfully
                ) else (
                        set VALIDATED_EXTENSION_LAST_VALUE=0
                )
        )

rem ERROR: At this point, all checks have failed and the file is not valid!
        set VAL_FILE_EXT_ERR_MSG=*** Validation of file “%VALIDATION_FILE%” failed because its extension is not one of: “%italics%%underline%%EXTENSION_LIST_TO_USE%%italics_off%%underline_off%”

        call divider
        call warning "Calling File: %_PBATCHNAME"                         silent
        call warning "  Parameters: %italics_on%%VEVPARAMS%%italics_off%" silent
        call warning "         CWD: %_CWD"                                silent

        iff "%CUSTOM_ERR_MSG%" == "" then
                echos %ANSI_COLOR_ERROR%
                call divider
                repeat  10  echo %VAL_FILE_EXT_ERR_MSG%%EOL%
                call divider
                call fatal_error %VAL_FILE_EXT_ERR_MSG%
                repeat 2 echo.
        else
                rem echos %ANSI_COLOR_FATAL_ERROR%
                call divider
                rem echos %ANSI_COLOR_FATAL_ERROR%
                call bigecho %ANSI_COLOR_FATAL_ERROR%%VAL_FILE_EXT_ERR_MSG%%ANSI_COLOR_NORMAL%
                rem echo  %ANSI_COLOR_FATAL_ERROR%
                call divider
                call fatal_error %CUSTOM_ERR_MSG%
                goto :END
                cancel
        endiff

:Validated_File_Extension_Successfully

:END
