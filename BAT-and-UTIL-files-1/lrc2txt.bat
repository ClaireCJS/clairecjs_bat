@Echo off
 call init-bat

rem Validate environment (once):
        iff 1 ne %validated_lrc2txt_env% then
                call validate-environment-variables EMOJIS_HAVE_BEEN_SET ANSI_COLORS_HAVE_BEEN_SET
                call validate-in-path               errorlevel.bat  lrc2txt.py  review-files.bat  approve-lyrics.bat python
                set  validated_lrc2txt_env=1
        endiff

rem Usage:
        iff "%1" eq "" then
                repeat 2 echo. %+ echo USAGE: lrc2txt whatever.lrc [silent]      %zzzzzz%   ━━   generates whatever.txt, if “silent” is 2nd option, then does so without post-review
                repeat 2 echo. %+ echo USAGE: lrc2txt -t                         %zzzzzz%   ━━   run testing suite (which is just about quote conversion right now)  
                repeat 2 echo. %+ echo USAGE: lrc2txt -a `|` -all `|` all `|` * `|` *.lrc   ━━   process all LRC files in the current directory
                echo.
                goto :END
        endiff

rem Parameter fetch:
        set OPTION=%@LOWER[%1]
        set PROCESS_ALL=0
        iff "%OPTION%" == "-a"  .or. "%OPTION%" == "-all" .or. "%OPTION%" == "all"  .or. "%OPTION%" == "*"  .or. "%OPTION%" == "*.lrc" then            %+ rem Check for the “all” option
                set PROCESS_ALL=1
        else
                set LRC_file=%@UNQUOTE[%1]
                set output_file=%@NAME[%lrc_file].txt
        endiff

rem Parameter validate:
        iff 0 eq %PROCESS_ALL% then 

                rem Validate input file:
                        call validate-environment-variable   LRC_file 
                        call validate-is-extension         "%LRC_file%"  *.lrc

                rem Prevent output file collision:
                        rem if exist "%output_file%" (call less_important "TXT file already exists: “%italics_on%%output_file%italics_off%”" %+ goto :END)
                        if exist "%Output_file%" (call deprecate "%output_file%" >nul lr>&>nul)

        endiff
        unset /q FILE_OR_FILES_TO_REVIEW
        

rem Cosmetics:
        if "%2" ne "silent" call divider
        
rem Perform the actual conversion:        
        rem lrc2txt.py "%LRC_file%"
        iff 1 eq %PROCESS_ALL% then
                for %%Ffff in (*.lrc) do (
                        rem echo Processing: "%Ffff"
                        lrc2txt.py       "%Ffff"
                        call ErrorLevel
                        set  expected_output_file=%@NAME[%FFFF].txt
                        echo expected_output_file="%expected_output_file%">nul
                        set FILE_OR_FILES_TO_REVIEW=%FILE_OR_FILES_TO_REVIEW% "%expected_output_file%"
                )
                rem set  FILE_OR_FILES_TO_REVIEW=*.txt
        else
                set  FILE_OR_FILES_TO_REVIEW="%OUTPUT_FILE%"
                lrc2txt.py "%LRC_file%"
                call ErrorLevel
                call validate-environment-variable FILE_OR_FILES_TO_REVIEW
        endiff


rem Review output:
        iff "%2" != "silent" then
                set first_file=1
                for %%tmp_review_file in (%file_or_files_to_review%) do (
                        set idea=maybe ask to hand-edit
                        if 1 eq %first_file% (
                                set first_file=2
                        ) else (
                                pause
                        )

                        rem Review generated file(s):proved, except sometimes:         
                                call review-files   "%@UNQUOTE[%tmp_review_file%]"                        

                        rem Mark generated file as approved, except sometimes:         
                                if "%Approve_Generated_Lyrics_CTLFKF%" ne "False" call approve-lyrics "%@UNQUOTE[%tmp_review_file%]"                        
                )
        endiff

:END
