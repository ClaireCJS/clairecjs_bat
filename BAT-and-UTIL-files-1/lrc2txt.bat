@Echo OFF

rem Validate environment (once):
        iff 1 ne %validated_lrc2txt_env% then
                call validate-environment-variables EMOJIS_HAVE_BEEN_SET ANSI_COLORS_HAVE_BEEN_SET
                call validate-in-path errorlevel lrc2txt.py review-files.bat
                set  validated_lrc2txt_env=1
        endiff

rem Usage:
        iff "%1" eq "" then
                repeat 2 echo.
                echo USAGE: lrc2txt whatever.lrc [silent] ━━ generates whatever.txt, if “silent” is 2nd option, then does so without post-review
                repeat 2 echo.
                echo USAGE: lrc2txt -t                    ━━ run testing suite (which is just about quote conversion right now)  
                echo.
                goto :END
        endiff

rem Parameter fetch:
        set    LRC_file=%@UNQUOTE[%1]
        set output_file=%@NAME[%lrc_file].txt

rem Parameter validate:
        iff "%lrc_file%" != "all" then
                call validate-environment-variable   LRC_file 
                call validate-is-extension         "%LRC_file%"  *.lrc
        endiff

rem Prevent file collision:
        if exist "%Output_file%" (call deprecate "%output_file%" >nul lr>&>nul)

rem Cosmetics:
        if "%2" ne "silent" call divider
        
rem Perform the actual conversion:        
        lrc2txt.py "%LRC_file%"

rem Validate output:
        call ErrorLevel
        iff "%LRC_FILE%" == "all" then
                set FILE_TO_REVIEW=*.txt
        endiff
        call validate-environment-variable output_file
        if "%2" ne "silent" call review-files "%FILE_TO_REVIEW%" "%output_file%"

:END
