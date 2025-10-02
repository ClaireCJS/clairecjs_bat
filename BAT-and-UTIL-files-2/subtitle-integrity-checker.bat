@Echo OFF
@LoadBTM on
@on break cancel


rem The main purpose for this wrapper script is to automatically insert the %_COLUMNS TCC auto-environment-variable into 
rem the command tail for subtitle-verifier.py, so that we don’t have to futz with Python’s awful console width detection libraries 




rem Get parameter:
        set subtitle_file_to_check=%@UNQUOTE[%1]


rem Validate parameter:
        if not exist "%subtitle_file_to_check%" call validate-environment-variable subtitle_file_to_check "1ˢᵗ argument to subtitle-integrity-checker must be a filename"

rem Validate environment once:
        iff "%validated_subtitle_integrety_checker%" != "1" then
                call validate-in-path subtitle-verifier.py
                set  validated_subtitle_integrety_checker=1
        endiff

rem Actually run it:
        subtitle-verifier.py -c %_COLUMNS "%subtitle_file_to_check%"



